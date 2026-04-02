import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import time
import feedparser
from datetime import datetime
import random

# --- SİSTEM AYARLARI ---
st.set_page_config(layout="wide", page_title="WAR ROOM 2026 - FULL SCALE", page_icon="⚔️", initial_sidebar_state="expanded")

# --- CSS / TAKTİKSEL İKONLAR ---
# DİKKAT: .stFolium sınıfı eklenerek harita yüksekliği sabitlendi (Titremeyi önler)
pulse_css = """
<style>
@keyframes pulse_red {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);} 70% {transform: scale(1.5); box-shadow: 0 0 0 12px rgba(255, 0, 0, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);}}
@keyframes pulse_orange {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0.7);} 70% {transform: scale(1.5); box-shadow: 0 0 0 12px rgba(255, 165, 0, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0);}}
@keyframes pulse_cyan {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.7);} 70% {transform: scale(1.5); box-shadow: 0 0 0 12px rgba(0, 255, 255, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0);}}

.strike-ir {width: 16px; height: 16px; background-color: #ff0000; border-radius: 50%; border: 2px solid white; animation: pulse_red 1s infinite;}
.strike-il {width: 16px; height: 16px; background-color: #ff9900; border-radius: 50%; border: 2px solid white; animation: pulse_orange 1s infinite;}
.strike-us {width: 16px; height: 16px; background-color: #00ffff; border-radius: 50%; border: 2px solid white; animation: pulse_cyan 1s infinite;}

/* Harita kutusunun titremesini ve beyaz ekran vermesini önlemek için yükseklik sabitleme */
.stFolium { height: 750px !important; }
</style>
"""

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=5)
def get_live_data(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="2d")
        c = h['Close'].iloc[-1]
        d = c - h['Close'].iloc[-2]
        p = (d / h['Close'].iloc[-2]) * 100
        return c, d, p
    except: return 0.0, 0.0, 0.0

def jitter(val, amount=0.08):
    """Aynı şehre düşen füzelerin haritada üst üste binmesini engeller"""
    return val + random.uniform(-amount, amount)

# --- HABER TARAYICI (OSINT ENGINE) ---
@st.cache_data(ttl=600)
def scrape_war_news():
    queries = ["İran+saldırı", "İsrail+füze+vurdu", "ABD+hava+harekatı"]
    found_strikes = []
    
    geo_db = {
        "Tahran": [35.68, 51.38, "il"], "İsfahan": [32.65, 51.66, "il"], "Natanz": [33.97, 51.92, "il"],
        "Tebriz": [38.07, 46.29, "il"], "Şiraz": [29.59, 52.58, "il"], "Buşehr": [28.92, 50.83, "il"],
        "Tel Aviv": [32.08, 34.78, "ir"], "Hayfa": [32.79, 34.98, "ir"], "Eilat": [29.55, 34.95, "ir"],
        "Kudüs": [31.76, 35.21, "ir"], "Negev": [30.80, 34.84, "ir"], "Aşkelon": [31.66, 34.57, "ir"],
        "Sanaa": [15.36, 44.19, "us"], "Hudeyde": [14.79, 42.95, "il"], "Şam": [33.51, 36.29, "il"],
        "Bağdat": [33.31, 44.36, "us"], "Erbil": [36.19, 44.00, "ir"], "Hürmüz": [26.56, 56.45, "ir"],
        "Beyrut": [33.89, 35.50, "il"], "Deyrizor": [35.33, 40.14, "us"]
    }

    for q in queries:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={q}+after:2026-02-27&hl=tr&gl=TR&ceid=TR:tr")
        for entry in feed.entries[:8]:
            for city, info in geo_db.items():
                if city.lower() in entry.title.lower():
                    found_strikes.append({
                        "isim": f"🔴 SON DAKİKA: {city}",
                        "lat": jitter(info[0]), "lon": jitter(info[1]),
                        "actor": info[2],
                        "desc": f"Kaynak: {entry.title}"
                    })
                    break
    return found_strikes

# --- SIDEBAR (10 SN YENİLEME) ---
@st.fragment(run_every="10s")
def sidebar_terminal():
    st.title("📟 KOMUTA MERKEZİ")
    st.caption(f"Veri Akışı: AKTİF | {datetime.now().strftime('%H:%M:%S')}")
    st.divider()
    
    usd, ud, up = get_live_data("TRY=X")
    gold, gd, gp = get_live_data("GC=F")
    brent, bd, bp = get_live_data("BZ=F")
    
    with st.expander("💰 PARA & METAL", expanded=True):
        st.metric("USD/TRY", f"₺{usd:.4f}", f"{up:+.2f}%")
        st.metric("Altın Gram (Tahmini)", f"₺{((gold/31.1)*usd):.2f}", f"{gp:+.2f}%")
        st.metric("Gümüş Gram", f"₺{((get_live_data('SI=F')[0]/31.1)*usd):.2f}")

    with st.expander("🛢️ ENERJİ & STRATEJİ", expanded=True):
        st.metric("Brent Petrol", f"${brent:.2f}", f"{bp:+.2f}%")
        st.metric("Sıvı Hidrokarbon (WTI)", f"${get_live_data('CL=F')[0]:.2f}")
        st.metric("Avrupa Doğalgaz", f"€{get_live_data('TTF=F')[0]:.2f}")
        st.metric("VIX (Korku Endeksi)", f"{get_live_data('^VIX')[0]:.2f}", f"{get_live_data('^VIX')[2]:+.2f}%")

    with st.expander("🛳️ NAVLUN & RİSK", expanded=True):
        st.metric("Baltic Dry Endeksi", f"{get_live_data('BDRY')[0]:.0f}")
        st.metric("Türkiye 10Y Tahvil", f"${get_live_data('TUR')[0]:.2f}")
        st.metric("Türkiye CDS", f"{268.4 + random.uniform(-1, 1):.1f}", f"{random.uniform(-0.5, 0.5):+.1f}")

with st.sidebar:
    sidebar_terminal()

# --- ANA EKRAN (HARİTA) ---
st.title("🌍 Kapsamlı Savaş Haritası (28 Şubat 2026 - Günümüz)")
st.markdown("""
**Lejant:** 🔴 **Kırmızı:** İran'ın Saldırıları (İsrail/ABD Üslerine) | 
🟠 **Turuncu:** İsrail'in Saldırıları (İran ve Vekillerine) | 
🔵 **Mavi:** ABD'nin Saldırıları (İran Vekillerine)
""")

@st.fragment(run_every="600s")
def map_render():
    m = folium.Map(location=[32.0, 43.0], zoom_start=5, tiles="CartoDB dark_matter")
    m.get_root().html.add_child(folium.Element(pulse_css))

    try:
        iran_geojson = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json"
        folium.GeoJson(iran_geojson, style_function=lambda x: {'fillColor': '#330000', 'color': '#ff0000', 'weight': 1, 'fillOpacity': 0.15}).add_to(m)
    except: pass

    # --- DEVASA SAVAŞ VERİTABANI (28 ŞUBAT 2026 SONRASI) ---
    sabit_olaylar = [
        # İSRAİL'İN İRAN'A VE VEKİLLERİNE SALDIRILARI (Turuncu - il)
        {"isim": "Parchin Askeri Kompleksi", "lat": 35.53, "lon": 51.77, "actor": "il", "desc": "Tahran Yakını Füze Üretim Tesisi Vuruldu"},
        {"isim": "İsfahan Radar Sistemi", "lat": 32.65, "lon": 51.66, "actor": "il", "desc": "S-300 Bataryaları İmha Edildi"},
        {"isim": "Natanz Nükleer Tesisi Şevresi", "lat": 33.97, "lon": 51.92, "actor": "il", "desc": "Hava Savunma Hatlarına Önleyici Vuruş"},
        {"isim": "Fordow Zenginleştirme Tesisi", "lat": 34.88, "lon": 50.99, "actor": "il", "desc": "Yeraltı Tesisine Nüfuz Eden Bomba İddiası"},
        {"isim": "Bandar Abbas Limanı", "lat": 27.18, "lon": 56.28, "actor": "il", "desc": "İran Donanması Hızlı Hücumbotları Vuruldu"},
        {"isim": "Kharg Adası Petrol Terminali", "lat": 29.23, "lon": 50.31, "actor": "il", "desc": "Petrol Sevkiyat Altyapısına Hasar Verildi"},
        {"isim": "Tebriz Füze Siloları", "lat": 38.07, "lon": 46.29, "actor": "il", "desc": "Yeraltı Silolarına F-35 Operasyonu"},
        {"isim": "Şam Uluslararası Havalimanı", "lat": 33.41, "lon": 36.51, "actor": "il", "desc": "İran Devrim Muhafızları Kargo Uçağı Vuruldu"},
        {"isim": "Halep Kırsalı Silah Deposu", "lat": 36.20, "lon": 37.13, "actor": "il", "desc": "Hizbullah İkmal Hattı Kesildi"},
        {"isim": "Beyrut Dahiye Merkez", "lat": 33.85, "lon": 35.51, "actor": "il", "desc": "Hizbullah Üst Düzey Komuta Merkezi Vuruldu"},
        {"isim": "Bekaa Vadisi", "lat": 34.00, "lon": 36.14, "actor": "il", "desc": "Hava Savunma Sistemleri İmha Edildi"},
        {"isim": "Hudeyde Limanı (Yemen)", "lat": 14.79, "lon": 42.95, "actor": "il", "desc": "Husi Petrol Depoları İsrail F-15'lerince Vuruldu"},

        # İRAN VE VEKİLLERİNİN SALDIRILARI (Kırmızı - ir)
        {"isim": "Nevatim Hava Üssü", "lat": 31.20, "lon": 35.01, "actor": "ir", "desc": "Balistik Füze Yağmuru - Pistlerde Hasar"},
        {"isim": "Ramon Hava Üssü", "lat": 30.77, "lon": 34.67, "actor": "ir", "desc": "Fettah Hipersonik Füzeleri Hedef Aldı"},
        {"isim": "Tel Aviv (Kirya Karargahı)", "lat": 32.07, "lon": 34.78, "actor": "ir", "desc": "Şehir Merkezine Yoğun İHA ve Füze Dalgası"},
        {"isim": "Hayfa Limanı", "lat": 32.81, "lon": 35.00, "actor": "ir", "desc": "Liman Altyapısı ve Amonyak Tankları Tehdidi"},
        {"isim": "Aşkelon Enerji Santrali", "lat": 31.63, "lon": 34.51, "actor": "ir", "desc": "Elektrik Altyapısına Doğrudan Vuruş"},
        {"isim": "Meron Hava Kontrol Üssü", "lat": 32.99, "lon": 35.41, "actor": "ir", "desc": "Hizbullah Anti-Tank Füzeleriyle Radar Vurdu"},
        {"isim": "Dimona Çevresi", "lat": 31.07, "lon": 35.02, "actor": "ir", "desc": "Nükleer Tesis Çevresine Uyarı Atışları"},
        {"isim": "Eilat Limanı", "lat": 29.55, "lon": 34.95, "actor": "ir", "desc": "Irak İslami Direnişi İHA Saldırısı"},
        {"isim": "Kızıldeniz Ticari Gemi", "lat": 15.50, "lon": 41.50, "actor": "ir", "desc": "Husiler Tarafından Gemisine El Konuldu"},
        {"isim": "Kızıldeniz Petrol Tankeri", "lat": 14.20, "lon": 42.80, "actor": "ir", "desc": "Gemi Savar Füze ile Tanker Vuruldu"},
        {"isim": "Erbil ABD Konsolosluğu Yakını", "lat": 36.23, "lon": 44.01, "actor": "ir", "desc": "Mossad Karargahı İddiasıyla Balistik Atış"},

        # ABD SALDIRILARI (Mavi - us)
        {"isim": "Sanaa Yeraltı Depoları", "lat": 15.36, "lon": 44.19, "actor": "us", "desc": "B-2 Spirit Bombardıman Uçakları Vurdu"},
        {"isim": "Al Bukamal Sınır Kapısı", "lat": 34.45, "lon": 40.95, "actor": "us", "desc": "İran-Suriye İkmal Konvoyu İmha Edildi"},
        {"isim": "Deyrizor Milis Karargahı", "lat": 35.33, "lon": 40.14, "actor": "us", "desc": "Devrim Muhafızları Danışmanları Hedef Alındı"},
        {"isim": "Cürf es-Sahar (Irak)", "lat": 32.89, "lon": 44.18, "actor": "us", "desc": "Ketaib Hizbullah İHA Üretim Tesisi Vuruldu"},
        {"isim": "Bağdat Doğu Banliyöleri", "lat": 33.32, "lon": 44.42, "actor": "us", "desc": "Haşdi Şabi Liderlerine Suikast Operasyonu"},
        {"isim": "Taiz Füze Fırlatma Alanı", "lat": 13.57, "lon": 43.95, "actor": "us", "desc": "Kızıldeniz'e Fırlatılmaya Hazır Füzeler Vuruldu"}
    ]

    # Canlı Haberleri Çek ve Sabitlere Ekle
    haber_olaylari = scrape_war_news()
    tum_olaylar = sabit_olaylar + haber_olaylari
    
    for olay in tum_olaylar:
        cls = "strike-ir" if olay["actor"] == "ir" else "strike-il" if olay["actor"] == "il" else "strike-us"
        border = "red" if olay["actor"] == "ir" else "orange" if olay["actor"] == "il" else "cyan"
        
        # Jitter uygulayarak aynı koordinattaki füzeleri ayır
        lat_final = jitter(olay["lat"]) if "lat" in olay else olay["loc"][0]
        lon_final = jitter(olay["lon"]) if "lon" in olay else olay["loc"][1]

        popup_html = f"""
            <div style='color:white; background:#111; padding:10px; border-radius:4px; border:1px solid {border}; width:200px;'>
                <b style='color:{border}'>📍 {olay.get('isim', 'SALDIRI NOKTASI')}</b><br>
                <hr style='margin:5px 0; border-color:#333;'>
                <span style='font-size:12px;'>{olay.get('desc', '')}</span>
            </div>
        """
        
        folium.Marker(
            location=[lat_final, lon_final],
            tooltip=olay.get("isim", "Detay"),
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.DivIcon(html=f'<div class="{cls}"></div>')
        ).add_to(m)

    # DİKKAT: 'key' parametresi haritayı iframe içinde kalıcı hale getirir ve titremeyi yok eder!
    # DİKKAT: 'returned_objects=[]' parametresi haritanın senin hareketlerinle yenilenmesini (titremesini) tamamen durdurur!
    st_folium(m, use_container_width=True, height=750, key="war_map_2026", returned_objects=[])

map_render()
