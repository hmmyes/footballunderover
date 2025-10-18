import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Sayfa yapılandırması
st.set_page_config(
    page_title="Under 4.5 Analiz",
    page_icon="⚽",
    layout="wide"
)

# API Bilgileri
API_KEY = "e8c410058cafbc96a86a8ddaef5fc029"
API_HOST = "v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': API_HOST,
    'x-rapidapi-key': API_KEY
}

# CSS Stilleri
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Önbellekleme için
@st.cache_data(ttl=60)
def get_live_matches():
    """Canlı maçları çeker"""
    url = f"https://{API_HOST}/fixtures"
    params = {"live": "all"}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        else:
            st.error(f"API Hatası: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_last_matches(team_id, last=10):
    """Takımın son maçlarını çeker"""
    url = f"https://{API_HOST}/fixtures"
    params = {
        "team": team_id,
        "last": last
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        return []
    except:
        return []

@st.cache_data(ttl=3600)
def get_h2h(team1_id, team2_id):
    """İki takımın karşılıklı maçlarını çeker"""
    url = f"https://{API_HOST}/fixtures/headtohead"
    params = {
        "h2h": f"{team1_id}-{team2_id}",
        "last": 10
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        return []
    except:
        return []

def calculate_under_over_stats(matches):
    """Under/Over istatistiklerini detaylı hesaplar"""
    if not matches:
        return {
            'under_15': 0, 'over_15': 0,
            'under_25': 0, 'over_25': 0,
            'under_35': 0, 'over_35': 0,
            'under_45': 0, 'over_45': 0,
            'total_matches': 0
        }
    
    stats = {
        'under_15': 0, 'over_15': 0,
        'under_25': 0, 'over_25': 0,
        'under_35': 0, 'over_35': 0,
        'under_45': 0, 'over_45': 0,
        'total_matches': 0
    }
    
    for match in matches:
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']
        if home_goals is not None and away_goals is not None:
            total = home_goals + away_goals
            stats['total_matches'] += 1
            
            if total < 2:
                stats['under_15'] += 1
            else:
                stats['over_15'] += 1
            
            if total < 3:
                stats['under_25'] += 1
            else:
                stats['over_25'] += 1
            
            if total < 4:
                stats['under_35'] += 1
            else:
                stats['over_35'] += 1
            
            if total < 5:
                stats['under_45'] += 1
            else:
                stats['over_45'] += 1
    
    total = stats['total_matches']
    if total > 0:
        stats['under_15_pct'] = round((stats['under_15'] / total) * 100, 1)
        stats['over_15_pct'] = round((stats['over_15'] / total) * 100, 1)
        stats['under_25_pct'] = round((stats['under_25'] / total) * 100, 1)
        stats['over_25_pct'] = round((stats['over_25'] / total) * 100, 1)
        stats['under_35_pct'] = round((stats['under_35'] / total) * 100, 1)
        stats['over_35_pct'] = round((stats['over_35'] / total) * 100, 1)
        stats['under_45_pct'] = round((stats['under_45'] / total) * 100, 1)
        stats['over_45_pct'] = round((stats['over_45'] / total) * 100, 1)
    
    return stats

def calculate_avg_goals(matches):
    """Ortalama gol sayısını hesaplar"""
    if not matches:
        return 0
    
    total_goals = 0
    valid_matches = 0
    for match in matches:
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']
        if home_goals is not None and away_goals is not None:
            total_goals += home_goals + away_goals
            valid_matches += 1
    
    return round(total_goals / valid_matches, 2) if valid_matches > 0 else 0

def get_under_percentage_by_type(stats, under_type):
    """Seçilen under türüne göre yüzdeyi döndürür"""
    if under_type == "Under 2.5":
        return stats.get('under_25_pct', 0)
    elif under_type == "Under 3.5":
        return stats.get('under_35_pct', 0)
    elif under_type == "Under 4.5":
        return stats.get('under_45_pct', 0)
    return 0

def analyze_match(match, min_under, min_min, max_min, min_gol, max_gol, avg_limit, under_type_param):
    """Maçı analiz eder ve öneri verir"""
    fixture = match['fixture']
    teams = match['teams']
    goals = match['goals']
    
    home_id = teams['home']['id']
    away_id = teams['away']['id']
    
    home_score = goals['home'] if goals['home'] is not None else 0
    away_score = goals['away'] if goals['away'] is not None else 0
    total_score = home_score + away_score
    
    elapsed = match['fixture']['status']['elapsed']
    if elapsed is None:
        elapsed = 0
    
    if not (min_gol <= total_score <= max_gol and min_min <= elapsed <= max_min):
        return None
    
    time.sleep(0.3)
    home_matches = get_team_last_matches(home_id)
    time.sleep(0.3)
    away_matches = get_team_last_matches(away_id)
    time.sleep(0.3)
    h2h_matches = get_h2h(home_id, away_id)
    
    home_stats = calculate_under_over_stats(home_matches)
    away_stats = calculate_under_over_stats(away_matches)
    h2h_stats = calculate_under_over_stats(h2h_matches)
    
    home_u = get_under_percentage_by_type(home_stats, under_type_param)
    away_u = get_under_percentage_by_type(away_stats, under_type_param)
    h2h_u = get_under_percentage_by_type(h2h_stats, under_type_param)
    
    home_avg = calculate_avg_goals(home_matches)
    away_avg = calculate_avg_goals(away_matches)
    combined_avg = round((home_avg + away_avg) / 2, 2)
    
    confidence = 0
    recommendation = "BEKLE"
    
    if home_u >= min_under and away_u >= min_under:
        confidence += 40
    elif home_u >= (min_under - 10) and away_u >= (min_under - 10):
        confidence += 25
    
    if h2h_u >= min_under:
        confidence += 30
    elif h2h_u >= (min_under - 10):
        confidence += 15
    
    if combined_avg <= avg_limit:
        confidence += 30
    elif combined_avg <= (avg_limit + 0.3):
        confidence += 15
    
    if total_score == 1 and elapsed <= (min_min + 15):
        confidence += 10
    
    if confidence >= 80:
        recommendation = "ÖNERİLİR ⭐⭐⭐"
    elif confidence >= 65:
        recommendation = "ÖNERİLİR ⭐⭐"
    elif confidence >= 50:
        recommendation = "DİKKATLE ⭐"
    else:
        recommendation = "ÖNERİLMEZ"
    
    return {
        'home_team': teams['home']['name'],
        'away_team': teams['away']['name'],
        'score': f"{home_score}-{away_score}",
        'minute': elapsed,
        'league': match['league']['name'],
        'home_u': home_u,
        'away_u': away_u,
        'h2h_u': h2h_u,
        'avg_goals': combined_avg,
        'confidence': confidence,
        'recommendation': recommendation,
        'home_stats': home_stats,
        'away_stats': away_stats,
        'h2h_stats': h2h_stats,
        'under_type': under_type_param
    }

# Sidebar - Ayarlar Paneli
st.sidebar.title("⚙️ Filtre Ayarları")
st.sidebar.markdown("---")

under_type = st.sidebar.selectbox(
    "🎯 Under Türü",
    options=["Under 2.5", "Under 3.5", "Under 4.5"],
    index=1,
    help="Hangi Under oranını takip etmek istiyorsunuz?"
)

under_threshold_map = {
    "Under 2.5": 2.5,
    "Under 3.5": 3.5,
    "Under 4.5": 4.5
}
under_threshold = under_threshold_map[under_type]

min_under_rate = st.sidebar.slider(
    f"Minimum {under_type} Oranı (%)",
    min_value=50,
    max_value=90,
    value=70,
    step=5,
    help=f"Takımların son maçlarında {under_type} bitme oranı"
)

st.sidebar.subheader("⏰ Dakika Aralığı")
min_minute = st.sidebar.number_input(
    "Minimum Dakika",
    min_value=1,
    max_value=45,
    value=10,
    step=1
)
max_minute = st.sidebar.number_input(
    "Maximum Dakika", 
    min_value=1,
    max_value=90,
    value=35,
    step=1
)

st.sidebar.subheader("⚽ Toplam Gol Sayısı")
min_goals = st.sidebar.number_input(
    "Minimum Gol",
    min_value=0,
    max_value=5,
    value=1,
    step=1
)
max_goals = st.sidebar.number_input(
    "Maximum Gol",
    min_value=0,
    max_value=5,
    value=2,
    step=1
)

avg_goal_limit = st.sidebar.slider(
    "Maximum Ortalama Gol",
    min_value=1.5,
    max_value=3.5,
    value=2.6,
    step=0.1,
    help="Takımların ortalama gol sayısı üst limiti"
)

st.sidebar.markdown("---")
st.sidebar.info(f"""
📊 **Mevcut Ayarlar:**
- Hedef: {under_type}
- Minimum Oran: ≥ %{min_under_rate}
- Dakika: {min_minute}-{max_minute}
- Gol: {min_goals}-{max_goals}
- Ort. Gol: ≤ {avg_goal_limit}
""")

st.title(f"⚽ {under_type} Canlı Analiz Sistemi")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"✅ {under_type} Oranı ≥ %{min_under_rate}")
with col2:
    st.info(f"⏰ Dakika: {min_minute}-{max_minute} arası")
with col3:
    st.info(f"⚽ Toplam Gol: {min_goals}-{max_goals}")

st.markdown("---")

if st.button("🔄 Canlı Maçları Yenile", type="primary"):
    st.cache_data.clear()

with st.spinner("Canlı maçlar yükleniyor..."):
    live_matches = get_live_matches()

if not live_matches:
    st.warning("⚠️ Şu anda canlı maç bulunamadı veya API bağlantısı sağlanamadı.")
    st.info("💡 API durumunu kontrol edin: https://dashboard.api-football.com/")
else:
    st.success(f"✅ {len(live_matches)} canlı maç bulundu. Analiz ediliyor...")
    
    recommended_matches = []
    
    progress_bar = st.progress(0)
    for idx, match in enumerate(live_matches[:30]):
        result = analyze_match(match, min_under_rate, min_minute, max_minute, min_goals, max_goals, avg_goal_limit, under_type)
        if result:
            recommended_matches.append(result)
        progress_bar.progress((idx + 1) / min(30, len(live_matches)))
    
    progress_bar.empty()
    
    if recommended_matches:
        st.success(f"🎯 {len(recommended_matches)} öneri bulundu!")
        
        df = pd.DataFrame(recommended_matches)
        df = df.sort_values('confidence', ascending=False)
        
        st.markdown("### 📊 Önerilen Maçlar")
        
        for idx, row in df.iterrows():
            if row['confidence'] >= 80:
                color = "🟢"
            elif row['confidence'] >= 65:
                color = "🟡"
            elif row['confidence'] >= 50:
                color = "🟠"
            else:
                color = "🔴"
            
            with st.expander(f"{color} **{row['home_team']} vs {row['away_team']}** - {row['score']} ({row['minute']}') - Güven: {row['confidence']}%"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Skor", row['score'])
                    st.metric("Dakika", f"{row['minute']}'")
                
                with col2:
                    st.metric(f"Ev Sahibi {row['under_type']}", f"{row['home_u']}%")
                    st.metric(f"Deplasman {row['under_type']}", f"{row['away_u']}%")
                
                with col3:
                    st.metric(f"H2H {row['under_type']}", f"{row['h2h_u']}%")
                    st.metric("Ort. Gol", row['avg_goals'])
                
                with col4:
                    st.metric("Güven Skoru", f"{row['confidence']}%")
                    st.markdown(f"### {row['recommendation']}")
                
                st.info(f"🏆 Lig: {row['league']}")
                
                st.markdown("---")
                st.markdown("### 📊 Detaylı Under/Over İstatistikleri (Son 10 Maç)")
                
                st.markdown(f"#### 🏠 {row['home_team']}")
                home_stats = row['home_stats']
                if home_stats['total_matches'] > 0:
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    with stats_col1:
                        st.metric("Under 1.5", f"{home_stats.get('under_15_pct', 0)}%", 
                                 f"{home_stats.get('under_15', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 1.5: {home_stats.get('over_15_pct', 0)}%")
                    with stats_col2:
                        st.metric("Under 2.5", f"{home_stats.get('under_25_pct', 0)}%",
                                 f"{home_stats.get('under_25', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 2.5: {home_stats.get('over_25_pct', 0)}%")
                    with stats_col3:
                        st.metric("Under 3.5", f"{home_stats.get('under_35_pct', 0)}%",
                                 f"{home_stats.get('under_35', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 3.5: {home_stats.get('over_35_pct', 0)}%")
                    with stats_col4:
                        st.metric("Under 4.5", f"{home_stats.get('under_45_pct', 0)}%",
                                 f"{home_stats.get('under_45', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 4.5: {home_stats.get('over_45_pct', 0)}%")
                else:
                    st.warning("Veri bulunamadı")
                
                st.markdown(f"#### ✈️ {row['away_team']}")
                away_stats = row['away_stats']
                if away_stats['total_matches'] > 0:
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    with stats_col1:
                        st.metric("Under 1.5", f"{away_stats.get('under_15_pct', 0)}%",
                                 f"{away_stats.get('under_15', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 1.5: {away_stats.get('over_15_pct', 0)}%")
                    with stats_col2:
                        st.metric("Under 2.5", f"{away_stats.get('under_25_pct', 0)}%",
                                 f"{away_stats.get('under_25', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 2.5: {away_stats.get('over_25_pct', 0)}%")
                    with stats_col3:
                        st.metric("Under 3.5", f"{away_stats.get('under_35_pct', 0)}%",
                                 f"{away_stats.get('under_35', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 3.5: {away_stats.get('over_35_pct', 0)}%")
                    with stats_col4:
                        st.metric("Under 4.5", f"{away_stats.get('under_45_pct', 0)}%",
                                 f"{away_stats.get('under_45', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 4.5: {away_stats.get('over_45_pct', 0)}%")
                else:
                    st.warning("Veri bulunamadı")
                
                st.markdown(f"#### 🤝 Karşılıklı Maçlar (H2H)")
                h2h_stats = row['h2h_stats']
                if h2h_stats['total_matches'] > 0:
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    with stats_col1:
                        st.metric("Under 1.5", f"{h2h_stats.get('under_15_pct', 0)}%",
                                 f"{h2h_stats.get('under_15', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 1.5: {h2h_stats.get('over_15_pct', 0)}%")
                    with stats_col2:
                        st.metric("Under 2.5", f"{h2h_stats.get('under_25_pct', 0)}%",
                                 f"{h2h_stats.get('under_25', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 2.5: {h2h_stats.get('over_25_pct', 0)}%")
                    with stats_col3:
                        st.metric("Under 3.5", f"{h2h_stats.get('under_35_pct', 0)}%",
                                 f"{h2h_stats.get('under_35', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 3.5: {h2h_stats.get('over_35_pct', 0)}%")
                    with stats_col4:
                        st.metric("Under 4.5", f"{h2h_stats.get('under_45_pct', 0)}%",
                                 f"{h2h_stats.get('under_45', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 4.5: {h2h_stats.get('over_45_pct', 0)}%")
                else:
                    st.warning("Karşılıklı maç verisi bulunamadı")
    else:
        st.warning("⚠️ Şu anda kriterlere uyan maç bulunamadı.")
        st.info("📌 Sistem 10-35 dakika arası, 1-2 gol atılmış ve yüksek Under oranına sahip maçları arar.")

st.markdown("---")
st.caption("⚠️ Bu sistem sadece bilgi amaçlıdır. Bahis kararlarınızı kendi sorumluluğunuzda alın.")
st.caption(f"🕐 Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")@st.cache_data(ttl=CACHE_DURATION)
def get_live_fixtures():
    url = f"{BASE_URL}/fixtures?live=all"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['response']
    else:
        st.error(f"Hata: Canlı maçlar çekilemedi. Status: {response.status_code}")
        return []

@st.cache_data(ttl=CACHE_DURATION)
def get_team_stats(team_id, last_matches=10):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&season=2024&league=39"  # Örnek league, değiştirilebilir
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stats = response.json()['response']
        # Son maçlar için under 3.5 hesapla (basitçe goals for + against < 4)
        under_count = 0
        total_matches = min(last_matches, len(stats.get('fixtures', [])))  # Fixtures yoksa hata önle
        for match in stats.get('fixtures', [])[:last_matches]:
            goals = match['goals']['home'] + match['goals']['away']
            if goals < 4:
                under_count += 1
        return under_count / total_matches if total_matches > 0 else 0
    return 0

@st.cache_data(ttl=CACHE_DURATION)
def get_h2h_stats(home_id, away_id, last_h2h=10):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={home_id}-{away_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        fixtures = response.json()['response']
        under_count = 0
        total_h2h = min(last_h2h, len(fixtures))
        for fixture in fixtures[:last_h2h]:
            goals = fixture['goals']['home'] + fixture['goals']['away']
            if goals < 4:
                under_count += 1
        return under_count / total_h2h if total_h2h > 0 else 0
    return 0

@st.cache_data(ttl=CACHE_DURATION)
def get_fixture_events(fixture_id):
    url = f"{BASE_URL}/fixtures/events?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['response']
    return []

def analyze_match(fixture, min_under_rate, gol_dakika_baslangic, gol_dakika_bitis, min_gol_sayisi, max_gol_sayisi, ort_gol_limiti):
    home_team = fixture['teams']['home']['id']
    away_team = fixture['teams']['away']['id']
    fixture_id = fixture['fixture']['id']
    current_minute = fixture['fixture']['status']['elapsed'] or 0
    
    # Erken gol kontrolü
    events = get_fixture_events(fixture_id)
    gol_sayisi = 0
    for event in events:
        if event['type'] == 'Goal' and gol_dakika_baslangic <= event['time']['elapsed'] <= gol_dakika_bitis:
            gol_sayisi += 1
    
    if not (min_gol_sayisi <= gol_sayisi <= max_gol_sayisi):
        return None  # Erken gol kriteri uymuyor
    
    # İstatistikler
    home_under_rate = get_team_stats(home_team) * 100
    away_under_rate = get_team_stats(away_team) * 100
    h2h_under_rate = get_h2h_stats(home_team, away_team) * 100
    
    avg_under_rate = (home_under_rate + away_under_rate + h2h_under_rate) / 3
    
    # Ortalama gol kontrolü (örnek olarak, takım stats'tan average goals al, ama basit tutalım)
    if avg_under_rate < min_under_rate:
        return None
    
    # Güven skoru: Basit ortalama
    guven_skoru = avg_under_rate
    
    # Öneri
    if guven_skoru >= guven_esikleri['yildiz_3']:
        oneri = "⭐⭐⭐"
    elif guven_skoru >= guven_esikleri['yildiz_2']:
        oneri = "⭐⭐"
    elif guven_skoru >= guven_esikleri['yildiz_1']:
        oneri = "⭐"
    else:
        oneri = ""
    
    return {
        "match": f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}",
        "current_score": f"{fixture['goals']['home']} - {fixture['goals']['away']}",
        "minute": current_minute,
        "under_rate": avg_under_rate,
        "guven_skoru": guven_skoru,
        "oneri": oneri
    }

# Ana uygulama
st.title("Under 4.5 Öneri AI Agent")

if st.button("Canlı Maçları Tara"):
    with st.spinner("Maçlar taranıyor..."):
        live_fixtures = get_live_fixtures()
        results = []
        for fixture in live_fixtures:
            result = analyze_match(fixture, min_under_rate, gol_dakika_baslangic, gol_dakika_bitis, min_gol_sayisi, max_gol_sayisi, ort_gol_limiti)
            if result:
                results.append(result)
        
        if results:
            df = pd.DataFrame(results)
            st.table(df)
        else:
            st.info("Kriterlere uyan maç bulunamadı.")

# Otomatik yenileme için (opsiyonel, Streamlit'te manuel button ile)
st.markdown("---")
st.caption("API-Football kullanılarak geliştirildi. Limitlere dikkat edin.")    cached = get_cached_data(endpoint, params)
    if cached:
        return cached
    
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            set_cache(endpoint, params, data)
            return data
        else:
            print(f"API Hata: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return None

# İsteğe Göre Ayarlanabilir CONFIG (Burayı değiştir!)
CONFIG = {
    'min_minute': 10,        # Erken gol min dakika
    'max_minute': 35,        # Erken gol max dakika
    'min_early_goals': 1,    # Min gol sayısı erken aşamada
    'max_early_goals': 2,    # Max gol sayısı erken aşamada
    'min_under_rate': 70,    # Under 3.5 min oranı (%) - BURAYI DEĞİŞTİR
    'confidence_thresholds': {
        '3_stars': 80,
        '2_stars': 65,
        '1_star': 50
    },
    'avg_goals_limit': 2.5   # Takım başına avg gol limiti
}

def get_live_matches():
    """Canlı maçları çek"""
    data = api_request('fixtures', {'live': 'all'})
    if data and data['response']:
        return data['response']
    return []

def get_match_statistics(league_id, season, team_id, last_n=10):
    """Takımın son N maç istatistikleri"""
    params = {
        'team': team_id,
        'last': last_n,
        'season': season
    }
    data = api_request('fixtures', params)
    if data and data['response']:
        matches = data['response'][-last_n:]  # Son N
        valid_matches = [m for m in matches if m['goals']['home'] is not None and m['goals']['away'] is not None]
        if not valid_matches:
            return {'under_rate': 0, 'avg_goals': 0, 'total_matches': 0}
        total_goals = sum(m['goals']['home'] + m['goals']['away'] for m in valid_matches)
        under_3_5 = sum(1 for m in valid_matches if (m['goals']['home'] + m['goals']['away']) < 3.5)
        under_rate = (under_3_5 / len(valid_matches)) * 100
        avg_goals = total_goals / len(valid_matches)
        return {
            'under_rate': under_rate,
            'avg_goals': avg_goals,
            'total_matches': len(valid_matches)
        }
    return {'under_rate': 0, 'avg_goals': 0, 'total_matches': 0}

def get_h2h_statistics(team1_id, team2_id, season, last_n=10):
    """H2H son N maç"""
    params = {
        'team1': team1_id,
        'team2': team2_id,
        'last': last_n
    }
    data = api_request('fixtures/head2head', params)
    if data and data['response']:
        matches = data['response'][-last_n:]
        valid_matches = [m for m in matches if m['goals']['home'] is not None and m['goals']['away'] is not None]
        if not valid_matches:
            return {'under_rate': 0, 'avg_goals': 0, 'total_matches': 0}
        total_goals = sum(m['goals']['home'] + m['goals']['away'] for m in valid_matches)
        under_3_5 = sum(1 for m in valid_matches if (m['goals']['home'] + m['goals']['away']) < 3.5)
        under_rate = (under_3_5 / len(valid_matches)) * 100
        avg_goals = total_goals / len(valid_matches)
        return {
            'under_rate': under_rate,
            'avg_goals': avg_goals,
            'total_matches': len(valid_matches)
        }
    return {'under_rate': 0, 'avg_goals': 0, 'total_matches': 0}

def analyze_match(fixture):
    """Tek maç analizi"""
    goals = fixture.get('goals', {})
    if goals.get('home') is None or goals.get('away') is None:
        return None
    
    current_minute = fixture.get('fixture', {}).get('minute', 0) or fixture.get('minute', 0)  # Farklı response'larda değişebilir
    total_goals = goals['home'] + goals['away']
    
    # Erken gol kontrolü (değiştirilebilir)
    if not (CONFIG['min_minute'] <= current_minute <= CONFIG['max_minute'] and 
            CONFIG['min_early_goals'] <= total_goals <= CONFIG['max_early_goals']):
        return None
    
    home_team_id = fixture['teams']['home']['id']
    away_team_id = fixture['teams']['away']['id']
    league_id = fixture['league']['id']
    season = fixture['league']['season']
    
    # İstatistikler
    home_stats = get_match_statistics(league_id, season, home_team_id)
    away_stats = get_match_statistics(league_id, season, away_team_id)
    h2h_stats = get_h2h_statistics(home_team_id, away_team_id, season)
    
    # Güven skoru hesabı
    under_rates = [home_stats['under_rate'], away_stats['under_rate'], h2h_stats['under_rate']]
    avg_under = sum(under_rates) / 3 if under_rates else 0
    
    score = 0
    if avg_under >= CONFIG['min_under_rate']:
        score += 50
    else:
        score += (avg_under / CONFIG['min_under_rate']) * 50
    
    # Ek kontroller
    if home_stats['avg_goals'] <= CONFIG['avg_goals_limit'] and away_stats['avg_goals'] <= CONFIG['avg_goals_limit']:
        score += 20
    if h2h_stats['avg_goals'] <= CONFIG['avg_goals_limit']:
        score += 15
    if h2h_stats['total_matches'] >= 3:  # H2H yeterli mi?
        score += 10
    if home_stats['total_matches'] >= 8 and away_stats['total_matches'] >= 8:  # Veri yeterli
        score += 5
    
    score = min(score, 100)  # Max 100
    
    return {
        'fixture': fixture,
        'confidence': score,
        'stats': {
            'home_under': home_stats['under_rate'],
            'away_under': away_stats['under_rate'],
            'h2h_under': h2h_stats['under_rate']
        }
    }

def get_stars(confidence):
    """Yıldız sistemi"""
    if confidence >= CONFIG['confidence_thresholds']['3_stars']:
        return '⭐⭐⭐'
    elif confidence >= CONFIG['confidence_thresholds']['2_stars']:
        return '⭐⭐'
    elif confidence >= CONFIG['confidence_thresholds']['1_star']:
        return '⭐'
    return ''

def get_recommendations():
    """Ana fonksiyon: Önerileri getir"""
    print("Canlı maçlar taranıyor...")
    live_matches = get_live_matches()
    recommendations = []
    
    for fixture in live_matches:
        analysis = analyze_match(fixture)
        if analysis:
            recommendations.append(analysis)
    
    # Güven skoru'na göre sırala (yüksekten düşüğe)
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    
    return recommendations

# Çalıştır
if __name__ == "__main__":
    print("=== Under 4.5 Öneri AI Agent ===")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    recommendations = get_recommendations()
    
    if not recommendations:
        print("❌ Kriterlere uyan maç yok (veya canlı maç yok). Farklı saat dene!")
    else:
        print(f"\n✅ {len(recommendations)} maç önerisi bulundu (Under 4.5 için bas!):")
        for i, rec in enumerate(recommendations, 1):
            fixture = rec['fixture']
            conf = rec['confidence']
            stars = get_stars(conf)
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            score = f"{fixture['goals']['home']}-{fixture['goals']['away']}"
            minute = fixture.get('minute', 0)
            print(f"\n{i}. {home} vs {away} ({minute}' - {score})")
            print(f"   Güven: {conf:.1f}/100 {stars}")
            print(f"   Under Oranları: Ev {rec['stats']['home_under']:.1f}%, Deplasman {rec['stats']['away_under']:.1f}%, H2H {rec['stats']['h2h_under']:.1f}%")
    
    print("\n=== Mevcut Ayarlar (Değiştirmek için CONFIG'i edit et) ===")
    for key, value in CONFIG.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for subkey, subval in value.items():
                print(f"  {subkey}: {subval}")
        else:
            print(f"{key}: {value}")
    print("Not: Under rate'i değiştirmek için 'min_under_rate' = yeni_değer yap. Gol dakikası için min/max_minute değiştir.")    }
</style>
""", unsafe_allow_html=True)

# Önbellekleme için
@st.cache_data(ttl=60)
def get_live_matches():
    """Canlı maçları çeker"""
    url = f"https://{API_HOST}/fixtures"
    params = {"live": "all"}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        else:
            st.error(f"API Hatası: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Bağlantı hatası: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_last_matches(team_id, last=10):
    """Takımın son maçlarını çeker"""
    url = f"https://{API_HOST}/fixtures"
    params = {
        "team": team_id,
        "last": last
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        return []
    except:
        return []

@st.cache_data(ttl=3600)
def get_h2h(team1_id, team2_id):
    """İki takımın karşılıklı maçlarını çeker"""
    url = f"https://{API_HOST}/fixtures/headtohead"
    params = {
        "h2h": f"{team1_id}-{team2_id}",
        "last": 10
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        return []
    except:
        return []

def calculate_under_over_stats(matches):
    """Under/Over istatistiklerini detaylı hesaplar"""
    if not matches:
        return {
            'under_15': 0, 'over_15': 0,
            'under_25': 0, 'over_25': 0,
            'under_35': 0, 'over_35': 0,
            'under_45': 0, 'over_45': 0,
            'total_matches': 0
        }
    
    stats = {
        'under_15': 0, 'over_15': 0,
        'under_25': 0, 'over_25': 0,
        'under_35': 0, 'over_35': 0,
        'under_45': 0, 'over_45': 0,
        'total_matches': 0
    }
    
    for match in matches:
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']
        if home_goals is not None and away_goals is not None:
            total = home_goals + away_goals
            stats['total_matches'] += 1
            
            if total < 2:
                stats['under_15'] += 1
            else:
                stats['over_15'] += 1
            
            if total < 3:
                stats['under_25'] += 1
            else:
                stats['over_25'] += 1
            
            if total < 4:
                stats['under_35'] += 1
            else:
                stats['over_35'] += 1
            
            if total < 5:
                stats['under_45'] += 1
            else:
                stats['over_45'] += 1
    
    total = stats['total_matches']
    if total > 0:
        stats['under_15_pct'] = round((stats['under_15'] / total) * 100, 1)
        stats['over_15_pct'] = round((stats['over_15'] / total) * 100, 1)
        stats['under_25_pct'] = round((stats['under_25'] / total) * 100, 1)
        stats['over_25_pct'] = round((stats['over_25'] / total) * 100, 1)
        stats['under_35_pct'] = round((stats['under_35'] / total) * 100, 1)
        stats['over_35_pct'] = round((stats['over_35'] / total) * 100, 1)
        stats['under_45_pct'] = round((stats['under_45'] / total) * 100, 1)
        stats['over_45_pct'] = round((stats['over_45'] / total) * 100, 1)
    
    return stats

def calculate_avg_goals(matches):
    """Ortalama gol sayısını hesaplar"""
    if not matches:
        return 0
    
    total_goals = 0
    valid_matches = 0
    for match in matches:
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']
        if home_goals is not None and away_goals is not None:
            total_goals += home_goals + away_goals
            valid_matches += 1
    
    return round(total_goals / valid_matches, 2) if valid_matches > 0 else 0

def get_under_percentage_by_type(stats, under_type):
    """Seçilen under türüne göre yüzdeyi döndürür"""
    if under_type == "Under 2.5":
        return stats.get('under_25_pct', 0)
    elif under_type == "Under 3.5":
        return stats.get('under_35_pct', 0)
    elif under_type == "Under 4.5":
        return stats.get('under_45_pct', 0)
    return 0

def analyze_match(match, min_under, min_min, max_min, min_gol, max_gol, avg_limit, under_type_param):
    """Maçı analiz eder ve öneri verir"""
    fixture = match['fixture']
    teams = match['teams']
    goals = match['goals']
    
    home_id = teams['home']['id']
    away_id = teams['away']['id']
    
    home_score = goals['home'] if goals['home'] is not None else 0
    away_score = goals['away'] if goals['away'] is not None else 0
    total_score = home_score + away_score
    
    elapsed = match['fixture']['status']['elapsed']
    if elapsed is None:
        elapsed = 0
    
    if not (min_gol <= total_score <= max_gol and min_min <= elapsed <= max_min):
        return None
    
    time.sleep(0.3)
    home_matches = get_team_last_matches(home_id)
    time.sleep(0.3)
    away_matches = get_team_last_matches(away_id)
    time.sleep(0.3)
    h2h_matches = get_h2h(home_id, away_id)
    
    home_stats = calculate_under_over_stats(home_matches)
    away_stats = calculate_under_over_stats(away_matches)
    h2h_stats = calculate_under_over_stats(h2h_matches)
    
    home_u = get_under_percentage_by_type(home_stats, under_type_param)
    away_u = get_under_percentage_by_type(away_stats, under_type_param)
    h2h_u = get_under_percentage_by_type(h2h_stats, under_type_param)
    
    home_avg = calculate_avg_goals(home_matches)
    away_avg = calculate_avg_goals(away_matches)
    combined_avg = round((home_avg + away_avg) / 2, 2)
    
    confidence = 0
    recommendation = "BEKLE"
    
    if home_u >= min_under and away_u >= min_under:
        confidence += 40
    elif home_u >= (min_under - 10) and away_u >= (min_under - 10):
        confidence += 25
    
    if h2h_u >= min_under:
        confidence += 30
    elif h2h_u >= (min_under - 10):
        confidence += 15
    
    if combined_avg <= avg_limit:
        confidence += 30
    elif combined_avg <= (avg_limit + 0.3):
        confidence += 15
    
    if total_score == 1 and elapsed <= (min_min + 15):
        confidence += 10
    
    if confidence >= 80:
        recommendation = "ÖNERİLİR ⭐⭐⭐"
    elif confidence >= 65:
        recommendation = "ÖNERİLİR ⭐⭐"
    elif confidence >= 50:
        recommendation = "DİKKATLE ⭐"
    else:
        recommendation = "ÖNERİLMEZ"
    
    return {
        'home_team': teams['home']['name'],
        'away_team': teams['away']['name'],
        'score': f"{home_score}-{away_score}",
        'minute': elapsed,
        'league': match['league']['name'],
        'home_u': home_u,
        'away_u': away_u,
        'h2h_u': h2h_u,
        'avg_goals': combined_avg,
        'confidence': confidence,
        'recommendation': recommendation,
        'home_stats': home_stats,
        'away_stats': away_stats,
        'h2h_stats': h2h_stats,
        'under_type': under_type_param
    }

# Sidebar - Ayarlar Paneli
st.sidebar.title("⚙️ Filtre Ayarları")
st.sidebar.markdown("---")

under_type = st.sidebar.selectbox(
    "🎯 Under Türü",
    options=["Under 2.5", "Under 3.5", "Under 4.5"],
    index=1,
    help="Hangi Under oranını takip etmek istiyorsunuz?"
)

under_threshold_map = {
    "Under 2.5": 2.5,
    "Under 3.5": 3.5,
    "Under 4.5": 4.5
}
under_threshold = under_threshold_map[under_type]

min_under_rate = st.sidebar.slider(
    f"Minimum {under_type} Oranı (%)",
    min_value=50,
    max_value=90,
    value=70,
    step=5,
    help=f"Takımların son maçlarında {under_type} bitme oranı"
)

st.sidebar.subheader("⏰ Dakika Aralığı")
min_minute = st.sidebar.number_input(
    "Minimum Dakika",
    min_value=1,
    max_value=45,
    value=10,
    step=1
)
max_minute = st.sidebar.number_input(
    "Maximum Dakika", 
    min_value=1,
    max_value=90,
    value=35,
    step=1
)

st.sidebar.subheader("⚽ Toplam Gol Sayısı")
min_goals = st.sidebar.number_input(
    "Minimum Gol",
    min_value=0,
    max_value=5,
    value=1,
    step=1
)
max_goals = st.sidebar.number_input(
    "Maximum Gol",
    min_value=0,
    max_value=5,
    value=2,
    step=1
)

avg_goal_limit = st.sidebar.slider(
    "Maximum Ortalama Gol",
    min_value=1.5,
    max_value=3.5,
    value=2.6,
    step=0.1,
    help="Takımların ortalama gol sayısı üst limiti"
)

st.sidebar.markdown("---")
st.sidebar.info(f"""
📊 **Mevcut Ayarlar:**
- Hedef: {under_type}
- Minimum Oran: ≥ %{min_under_rate}
- Dakika: {min_minute}-{max_minute}
- Gol: {min_goals}-{max_goals}
- Ort. Gol: ≤ {avg_goal_limit}
""")

st.title(f"⚽ {under_type} Canlı Analiz Sistemi")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"✅ {under_type} Oranı ≥ %{min_under_rate}")
with col2:
    st.info(f"⏰ Dakika: {min_minute}-{max_minute} arası")
with col3:
    st.info(f"⚽ Toplam Gol: {min_goals}-{max_goals}")

st.markdown("---")

if st.button("🔄 Canlı Maçları Yenile", type="primary"):
    st.cache_data.clear()

with st.spinner("Canlı maçlar yükleniyor..."):
    live_matches = get_live_matches()

if not live_matches:
    st.warning("⚠️ Şu anda canlı maç bulunamadı veya API bağlantısı sağlanamadı.")
    st.info("💡 API durumunu kontrol edin: https://dashboard.api-football.com/")
else:
    st.success(f"✅ {len(live_matches)} canlı maç bulundu. Analiz ediliyor...")
    
    recommended_matches = []
    
    progress_bar = st.progress(0)
    for idx, match in enumerate(live_matches[:30]):
        result = analyze_match(match, min_under_rate, min_minute, max_minute, min_goals, max_goals, avg_goal_limit, under_type)
        if result:
            recommended_matches.append(result)
        progress_bar.progress((idx + 1) / min(30, len(live_matches)))
    
    progress_bar.empty()
    
    if recommended_matches:
        st.success(f"🎯 {len(recommended_matches)} öneri bulundu!")
        
        df = pd.DataFrame(recommended_matches)
        df = df.sort_values('confidence', ascending=False)
        
        st.markdown("### 📊 Önerilen Maçlar")
        
        for idx, row in df.iterrows():
            if row['confidence'] >= 80:
                color = "🟢"
            elif row['confidence'] >= 65:
                color = "🟡"
            elif row['confidence'] >= 50:
                color = "🟠"
            else:
                color = "🔴"
            
            with st.expander(f"{color} **{row['home_team']} vs {row['away_team']}** - {row['score']} ({row['minute']}') - Güven: {row['confidence']}%"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Skor", row['score'])
                    st.metric("Dakika", f"{row['minute']}'")
                
                with col2:
                    st.metric(f"Ev Sahibi {row['under_type']}", f"{row['home_u']}%")
                    st.metric(f"Deplasman {row['under_type']}", f"{row['away_u']}%")
                
                with col3:
                    st.metric(f"H2H {row['under_type']}", f"{row['h2h_u']}%")
                    st.metric("Ort. Gol", row['avg_goals'])
                
                with col4:
                    st.metric("Güven Skoru", f"{row['confidence']}%")
                    st.markdown(f"### {row['recommendation']}")
                
                st.info(f"🏆 Lig: {row['league']}")
                
                st.markdown("---")
                st.markdown("### 📊 Detaylı Under/Over İstatistikleri (Son 10 Maç)")
                
                st.markdown(f"#### 🏠 {row['home_team']}")
                home_stats = row['home_stats']
                if home_stats['total_matches'] > 0:
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    with stats_col1:
                        st.metric("Under 1.5", f"{home_stats.get('under_15_pct', 0)}%", 
                                 f"{home_stats.get('under_15', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 1.5: {home_stats.get('over_15_pct', 0)}%")
                    with stats_col2:
                        st.metric("Under 2.5", f"{home_stats.get('under_25_pct', 0)}%",
                                 f"{home_stats.get('under_25', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 2.5: {home_stats.get('over_25_pct', 0)}%")
                    with stats_col3:
                        st.metric("Under 3.5", f"{home_stats.get('under_35_pct', 0)}%",
                                 f"{home_stats.get('under_35', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 3.5: {home_stats.get('over_35_pct', 0)}%")
                    with stats_col4:
                        st.metric("Under 4.5", f"{home_stats.get('under_45_pct', 0)}%",
                                 f"{home_stats.get('under_45', 0)}/{home_stats['total_matches']}")
                        st.caption(f"Over 4.5: {home_stats.get('over_45_pct', 0)}%")
                else:
                    st.warning("Veri bulunamadı")
                
                st.markdown(f"#### ✈️ {row['away_team']}")
                away_stats = row['away_stats']
                if away_stats['total_matches'] > 0:
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    with stats_col1:
                        st.metric("Under 1.5", f"{away_stats.get('under_15_pct', 0)}%",
                                 f"{away_stats.get('under_15', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 1.5: {away_stats.get('over_15_pct', 0)}%")
                    with stats_col2:
                        st.metric("Under 2.5", f"{away_stats.get('under_25_pct', 0)}%",
                                 f"{away_stats.get('under_25', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 2.5: {away_stats.get('over_25_pct', 0)}%")
                    with stats_col3:
                        st.metric("Under 3.5", f"{away_stats.get('under_35_pct', 0)}%",
                                 f"{away_stats.get('under_35', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 3.5: {away_stats.get('over_35_pct', 0)}%")
                    with stats_col4:
                        st.metric("Under 4.5", f"{away_stats.get('under_45_pct', 0)}%",
                                 f"{away_stats.get('under_45', 0)}/{away_stats['total_matches']}")
                        st.caption(f"Over 4.5: {away_stats.get('over_45_pct', 0)}%")
                else:
                    st.warning("Veri bulunamadı")
                
                st.markdown(f"#### 🤝 Karşılıklı Maçlar (H2H)")
                h2h_stats = row['h2h_stats']
                if h2h_stats['total_matches'] > 0:
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    with stats_col1:
                        st.metric("Under 1.5", f"{h2h_stats.get('under_15_pct', 0)}%",
                                 f"{h2h_stats.get('under_15', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 1.5: {h2h_stats.get('over_15_pct', 0)}%")
                    with stats_col2:
                        st.metric("Under 2.5", f"{h2h_stats.get('under_25_pct', 0)}%",
                                 f"{h2h_stats.get('under_25', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 2.5: {h2h_stats.get('over_25_pct', 0)}%")
                    with stats_col3:
                        st.metric("Under 3.5", f"{h2h_stats.get('under_35_pct', 0)}%",
                                 f"{h2h_stats.get('under_35', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 3.5: {h2h_stats.get('over_35_pct', 0)}%")
                    with stats_col4:
                        st.metric("Under 4.5", f"{h2h_stats.get('under_45_pct', 0)}%",
                                 f"{h2h_stats.get('under_45', 0)}/{h2h_stats['total_matches']}")
                        st.caption(f"Over 4.5: {h2h_stats.get('over_45_pct', 0)}%")
                else:
                    st.warning("Karşılıklı maç verisi bulunamadı")
    else:
        st.warning("⚠️ Şu anda kriterlere uyan maç bulunamadı.")
        st.info("📌 Sistem 10-35 dakika arası, 1-2 gol atılmış ve yüksek Under oranına sahip maçları arar.")

st.markdown("---")
st.caption("⚠️ Bu sistem sadece bilgi amaçlıdır. Bahis kararlarınızı kendi sorumluluğunuzda alın.")
st.caption(f"🕐 Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
