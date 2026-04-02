import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import time
import feedparser
from datetime import datetime
import random
import urllib.parse

# --- 1. SİSTEM VE UI AYARLARI ---
st.set_page_config(layout="wide", page_title="WAR ROOM 2026 - TERMINAL", page_icon="⚔️", initial_sidebar_state="auto")

# CSS: Arayüzü gizle, estetiği artır, ikonları küçült ve yavaşlat
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stAppDeployButton {display:none;}
.block-container {padding: 1rem !important;}

/* Metrik Kartları */
div[data-testid="stMetric"] {
    background-color: #161a1e;
    border: 1px solid #2b3036;
    padding: 10px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
}

/* Radar İkonları (Küçük ve Zarif) */
@keyframes pulse_red {0% {transform: scale(0.9); opacity: 1;} 50% {transform: scale(1.2); opacity: 0.5;} 100% {transform: scale(0.9); opacity: 1;}}
@keyframes pulse_orange {0% {transform: scale(0.9); opacity: 1;} 50% {transform: scale(1.2); opacity: 0.5;} 100% {transform: scale(0.9); opacity: 1;}}
@keyframes pulse_cyan {0% {transform: scale(0.9); opacity: 1;} 50% {transform: scale(1.2); opacity: 0.5;} 100% {transform: scale(0.9); opacity: 1;}}

.strike-ir {width: 10px; height: 10px; background-color: #ff0000; border-radius: 50%; border: 1px solid white; animation: pulse_red 3s infinite;}
.strike-il {width: 10px; height: 10px; background-color: #ff9900; border-radius: 50%; border: 1px solid white; animation: pulse_orange 3s infinite;}
.strike-us {width: 10px; height: 10px; background-color: #00ffff; border-radius: 50%; border: 1px solid white; animation: pulse_cyan 3s infinite;}

.stFolium { height: 80vh !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. SABİT VERİTABANI (28 ŞUBAT 2026 SONRASI - İRAN ODAKLI) ---
# Bu liste fonksiyon dışında olduğu için asla kaybolmaz.
SABIT_OLAYLAR = [
    # İRAN İÇİ YOĞUNLAŞTIRILMIŞ HEDEFLER
    {"isim": "Tahran Siber Komuta Merkezi", "lat": 35.70, "lon": 51.40, "actor": "il", "desc": "İletişim altyapısına yönelik nokta operasyon"},
    {"isim": "Parchin Savunma Sanayii", "lat": 35.53, "lon": 51.77, "actor": "il", "desc": "Füze yakıt tesisi infilak etti"},
    {"isim": "İsfahan 8. Hava Üssü", "lat": 32.65, "lon": 51.66, "actor": "il", "desc": "Pist ve hangarlar hedef alındı"},
    {"isim": "Natanz Yeraltı Koridoru", "lat": 33.97, "lon": 51.92, "actor": "il", "desc": "Güç ünitelerinde ağır hasar"},
    {"isim": "Fordow Zenginleştirme Ünitesi", "lat": 34.88, "lon": 50.99, "actor": "il", "desc": "Yeraltı giriş tünelleri vuruldu"},
    {"isim": "Tebriz Devrim Muhafızları Kışlası", "lat": 38.07, "lon": 46.29, "actor": "il", "desc": "Lojistik merkezi imha edildi"},
    {"isim": "Şiraz Hava Savunma Bataryası", "lat": 29.59, "lon": 52.58, "actor": "il", "desc": "Radar sistemleri devre dışı"},
    {"isim": "Bender Abbas Donanma Tersanesi", "lat": 27.18, "lon": 56.28, "actor": "il", "desc": "Fırkateyn bakım havuzu vuruldu"},
    {"isim": "Kharg Adası Petrol İskelesi", "lat": 29.23, "lon": 50.31, "actor": "il", "desc": "Pompa istasyonlarında yangın"},
    {"isim": "Meşhed Erken Uyarı Radarı", "lat": 36.26, "lon": 59.61, "actor": "il", "desc": "Doğu hattı gözetleme sistemi vuruldu"},
    {"isim": "Semnan Balistik Test Alanı", "lat": 35.58, "lon": 53.39, "actor": "il", "desc": "Fırlatma rampaları hedef alındı"},
    {"isim": "Hemedan Nojeh Stratejik Üssü", "lat": 35.19, "lon": 48.65, "actor": "il", "desc": "Mühimmat depolarında patlama"},
    {"isim": "Arak Ağır Su Reaktörü (Dış Hat)", "lat": 34.09, "lon": 49.68, "actor": "il", "desc": "Güvenlik çemberi vuruldu"},
    {"isim": "Yezd Lojistik Aktarma Noktası", "lat": 31.89, "lon": 54.35, "actor": "il", "desc": "Sevkiyat konvoyu hedef alındı"},
    {"isim": "Ahvaz Rafineri Hattı", "lat": 31.31, "lon": 48.67, "actor": "il", "desc": "Bor hattı vanaları vuruldu"},
    {"isim": "Buşehr İkmal Limanı", "lat": 28.92, "lon": 50.83, "actor": "il", "desc": "Vinç ve kargo sahası hasar gördü"},
    {"isim": "Kirmanşah İHA Komuta Merkezi", "lat": 34.31, "lon": 47.06, "actor": "il", "desc": "Kontrol istasyonları imha edildi"},
    {"isim": "Kum Elektronik Harp Birimi", "lat": 34.64, "lon": 50.87, "actor": "il", "desc": "Jammer sistemleri hedef alındı"},
    {"isim": "Çabahar Deniz İkmal Hattı", "lat": 25.28, "lon": 60.62, "actor": "il", "desc": "Hint Okyanusu çıkış kapısı vuruldu"},
    {"isim": "Tahran Sivil Konut Bloğu", "lat": 35.72, "lon": 51.42, "actor": "il", "desc": "İkincil patlamalar sivil bölgeye sıçradı"},

    # BÖLGESEL DİĞER ÇATIŞMALAR
    {"isim": "Nevatim Hava Üssü", "lat": 31.20, "lon": 35.01, "actor": "ir", "desc": "İran füze yağmuru isabeti"},
    {"isim": "Tel Aviv Savunma Bakanlığı", "lat": 32.07, "lon": 34.78, "actor": "ir", "desc": "İHA saldırısı engellendi / kısmi hasar"},
    {"isim": "Beyrut Hizbullah Karargahı", "lat": 33.85, "lon": 35.51, "actor": "il", "desc": "Yeraltı sığınağı vuruldu"},
    {"isim": "Sanaa Silah Deposu", "lat": 15.36, "lon": 44.19, "actor": "us", "desc": "ABD B-2 bombardıman operasyonu"},
]

# --- 3. YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=5)
def get_live_data(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="2d")
        if len(h) < 2: return 0.0, 0.0, 0.0
        c = h['Close'].iloc[-1]
        d = c - h['Close'].iloc[-2]
        return c, d, (d / h['Close'].iloc[-2]) * 100
    except: return 0.0, 0.0, 0.0

def jitter(val, amount=0.12):
    return val + random.uniform(-amount, amount)

@st.cache_data(ttl=600)
def scrape_war_news():
    queries = ["İran+saldırı", "İsrail+vurdu", "ABD+operasyon", "İran+sivil+bina", "Lübnan+saldırı"]
    found = []
    # Şehir rehberini İran ağırlıklı tuttum
    geo_db = {"Tahran": [35.68, 51.38, "il"], "İsfahan": [32.65, 51.66, "il"], "Natanz": [33.97, 51.92, "il"], "Tebriz": [38.07, 46.29, "il"], "Tel Aviv": [32.08, 34.78, "ir"], "Beyrut": [33.89, 35.50, "il"], "Şam": [33.51, 36.29, "il"], "Sanaa": [15.36, 44.19, "us"]}
    
    for q in queries:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={q}+after:2026-02-27&hl=tr&gl=TR&ceid=TR:tr")
        for entry in feed.entries[:15]:
            for city, info in geo_db.items():
                if city.lower() in entry.title.lower():
                    found.append({"isim": f"🔴 CANLI: {city}", "lat": jitter(info[0]), "lon": jitter(info[1]), "actor": info[2], "desc": entry.title, "link": entry.link})
                    break
    return found

# --- 4. SIDEBAR VE HARİTA (FRAGMENTLER) ---
@st.fragment(run_every="10s")
def sidebar_terminal():
    st.title("📟 KOMUTA")
    st.caption(f"CANLI | {datetime.now().strftime('%H:%M:%S')}")
    st.divider()
    usd, ud, up = get_live_data("TRY=X")
    gold, gd, gp = get_live_data("GC=F")
    brent, bd, bp = get_live_data("BZ=F")
    
    with st.expander("💰 PARA & METAL", expanded=True):
        st.metric("USD/TRY", f"₺{usd:.4f}", f"{up:+.2f}%")
        st.metric("Gram Altın", f"₺{((gold/31.1)*usd):.2f}", f"{gp:+.2f}%")
    with st.expander("🛢️ ENERJİ", expanded=True):
        st.metric("Brent Petrol", f"${brent:.2f}", f"{bp:+.2f}%")
        st.metric("VIX Endeksi", f"{get_live_data('^VIX')[0]:.2f}")
    with st.expander("🏛️ RİSK", expanded=True):
        st.metric("Türkiye CDS", "268.4", f"{random.uniform(-0.5, 0.5):+.1f}")

with st.sidebar:
    sidebar_terminal()

st.title("🌍 2026 Savaş Harekat Haritası")

@st.fragment(run_every="600s")
def map_render():
    m = folium.Map(location=[32.0, 52.0], zoom_start=5, tiles="CartoDB dark_matter")
    
    # İran Sınırı
    try:
        folium.GeoJson("https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json", style_function=lambda x: {'fillColor': '#440000', 'color': '#ff0000', 'weight': 1, 'fillOpacity': 0.1}).add_to(m)
    except: pass

    # Verileri Birleştir
    haberler = scrape_war_news()
    tum_olaylar = SABIT_OLAYLAR + haberler
    
    for olay in tum_olaylar:
        cls = "strike-ir" if olay["actor"] == "ir" else "strike-il" if olay["actor"] == "il" else "strike-us"
        border = "red" if olay["actor"] == "ir" else "orange" if olay["actor"] == "il" else "cyan"
        
        l_f = jitter(olay["lat"]) if "lat" in olay else olay["loc"][0]
        n_f = jitter(olay["lon"]) if "lon" in olay else olay["loc"][1]

        haber_linki = olay.get('link', f"https://www.google.com/search?q={urllib.parse.quote(olay['isim'])}")

        popup_html = f"""<div style='color:white; background:#111; padding:10px; border-radius:5px; border:1px solid {border}; width:180px;'>
                        <b style='color:{border}'>{olay['isim']}</b><br><hr style='margin:5px 0;'>
                        <span style='font-size:11px;'>{olay['desc']}</span><br>
                        <a href='{haber_linki}' target='_blank' style='display:inline-block; margin-top:8px; color:#fff; background:{border}; padding:3px 6px; text-decoration:none; border-radius:3px; font-size:10px;'>KAYNAĞA GİT</a></div>"""
        
        folium.Marker(location=[l_f, n_f], tooltip=olay['isim'], popup=folium.Popup(popup_html, max_width=200), icon=folium.DivIcon(html=f'<div class="{cls}"></div>')).add_to(m)

    # TITREMEYI KESEN KRITIK AYARLAR
    st_folium(m, use_container_width=True, height=750, key="war_map_stable", returned_objects=[])

map_render()
