import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import time
import feedparser
from datetime import datetime
import random

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Global OSINT & Market Command", page_icon="🌍", initial_sidebar_state="expanded")

# --- CSS VE ANİMASYONLAR (HARİTA İKONLARI İÇİN) ---
# Farklı ülkelerin saldırıları ve üsleri için özel parlayan (glowing) ikon tasarımları
pulse_css = """
<style>
@keyframes pulse_red {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);} 70% {transform: scale(1.2); box-shadow: 0 0 0 10px rgba(255, 0, 0, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);}}
@keyframes pulse_orange {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0.7);} 70% {transform: scale(1.2); box-shadow: 0 0 0 10px rgba(255, 165, 0, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0);}}
@keyframes pulse_cyan {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.7);} 70% {transform: scale(1.2); box-shadow: 0 0 0 10px rgba(0, 255, 255, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0);}}

.icon-iran-strike {width: 18px; height: 18px; background-color: #ff0000; border-radius: 50%; border: 2px solid white; animation: pulse_red 1.5s infinite;}
.icon-israel-strike {width: 18px; height: 18px; background-color: #ff9900; border-radius: 50%; border: 2px solid white; animation: pulse_orange 1.5s infinite;}
.icon-us-strike {width: 18px; height: 18px; background-color: #00ffff; border-radius: 50%; border: 2px solid white; animation: pulse_cyan 1.5s infinite;}
.icon-base {width: 14px; height: 14px; background-color: #aaaaaa; border-radius: 0%; border: 2px solid white;} /* Üsler kare ve sabit */
</style>
"""

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=5) # Yahoo verilerini çok hızlı tazeler
def get_finance_data(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="5d")
        if len(h) >= 2:
            close = float(h['Close'].iloc[-1])
            prev = float(h['Close'].iloc[-2])
            return close, close - prev, ((close - prev) / prev) * 100
        return 0.0, 0.0, 0.0
    except:
        return 0.0, 0.0, 0.0

def calculate_gram_prices():
    usd_fiyat, _, _ = get_finance_data("TRY=X")
    gold_ons, _, _ = get_finance_data("GC=F")
    silver_ons, _, _ = get_finance_data("SI=F")
    gram_altin = (gold_ons / 31.1035) * usd_fiyat if usd_fiyat > 0 else 0
    gram_gumus = (silver_ons / 31.1035) * usd_fiyat if usd_fiyat > 0 else 0
    return gram_altin, gram_gumus, usd_fiyat

def metric_box(label, symbol, formatter="${:.2f}"):
    c, d, p = get_finance_data(symbol)
    st.metric(label, formatter.format(c), f"{d:+.2f} ({p:+.2f}%)")

# --- CANLI PANEL (FRAGMENT: Sadece burası 10 saniyede bir yenilenir, harita donmaz) ---
@st.fragment(run_every="10s")
def render_live_sidebar():
    st.sidebar.title("📟 CANLI TERMİNAL")
    st.sidebar.caption(f"🔴 CANLI | Son Tik: {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.divider()
    
    gram_altin, gram_gumus, usd_try = calculate_gram_prices()

    with st.sidebar.expander("🛢️ ENERJİ & NAVLUN", expanded=True):
        metric_box("Brent Vadeli", "BZ=F")
        metric_box("Brent Spot (Proxy BNO)", "BNO")
        metric_box("Sıvı Hidrokarbon (WTI)", "CL=F")
        metric_box("Avrupa Doğalgaz (TTF)", "TTF=F", "€{:.2f}")
        metric_box("Jet Yakıtı (Proxy HO)", "HO=F")
        metric_box("Baltic Dry Endeksi", "BDRY", "{:.2f}")

    with st.sidebar.expander("🚢 HÜRMÜZ TRAFİĞİ (Simüle)", expanded=True):
        st.metric("⬅️ Batıya Giden Tanker", 14 + random.randint(-1, 1), random.randint(-1, 1))
        st.metric("➡️ Doğuya Giden Tanker", 11 + random.randint(-1, 1), random.randint(-1, 1))

    with st.sidebar.expander("🏗️ ENDÜSTRİYEL & TARIM", expanded=False):
        metric_box("Alüminyum", "ALI=F")
        metric_box("Gübre (CF Ind.)", "CF")
        metric_box("Polyester (Celanese Proxy)", "CE")

    with st.sidebar.expander("💰 METALLER & DÖVİZ", expanded=True):
        st.metric("Altın Gram", f"₺{gram_altin:.2f}")
        st.metric("Gümüş Gram", f"₺{gram_gumus:.2f}")
        metric_box("USD/TRY", "TRY=X", "₺{:.4f}")

    with st.sidebar.expander("🏛️ RİSK & TAHVİL", expanded=True):
        metric_box("VIX (Korku Endeksi)", "^VIX", "{:.2f}")
        metric_box("ABD 10Y Tahvil", "^TNX", "%{:.2f}")
        metric_box("Türkiye 10Y (TUR Proxy)", "TUR", "${:.2f}")
        st.metric("Türkiye CDS (Simüle)", f"{265.4 + random.uniform(-2, 2):.1f}", f"{random.uniform(-1, 1):+.1f}")

# Yan menüyü çalıştır
render_live_sidebar()

# --- ANA EKRAN VE HARİTA ---
st.title("🗺️ Kapsamlı Çatışma ve Strateji Haritası")
st.markdown("""
**Lejant:** ⚪ **Kare İkon:** Askeri Üsler | 
🔴 **Kırmızı:** İran'ın Saldırıları | 
🟠 **Turuncu:** İsrail'in Saldırıları | 
🔵 **Mavi:** ABD'nin Saldırıları
""")

# Kapsamlı Veritabanı (Senin isteğin üzerine ÇOK SAYIDA nokta eklendi)
olaylar_ve_usler = [
    # --- ASKERİ ÜSLER (GRI KARE) ---
    {"isim": "Al Udeid Hava Üssü (Katar)", "lat": 25.11, "lon": 51.31, "tip": "us", "detay": "ABD Merkez Kuvvetler Karargahı"},
    {"isim": "NSA Bahreyn", "lat": 26.21, "lon": 50.60, "tip": "us", "detay": "ABD 5. Filo Karargahı"},
    {"isim": "Al Asad Hava Üssü (Irak)", "lat": 33.79, "lon": 42.43, "tip": "us", "detay": "ABD ve Koalisyon Güçleri"},
    {"isim": "Nevatim Hava Üssü (İsrail)", "lat": 31.20, "lon": 35.01, "tip": "us", "detay": "F-35 Filosu ve Nükleer Kapasite"},
    {"isim": "Hatzerim Hava Üssü (İsrail)", "lat": 31.23, "lon": 34.66, "tip": "us", "detay": "İsrail Hava Kuvvetleri"},
    {"isim": "Bandar Abbas (İran)", "lat": 27.18, "lon": 56.28, "tip": "us", "detay": "İran Donanma Merkez Üssü"},
    {"isim": "Tebriz Hava Üssü (İran)", "lat": 38.13, "lon": 46.23, "tip": "us", "detay": "İran Hava Kuvvetleri"},
    {"isim": "İncirlik Hava Üssü (Türkiye)", "lat": 37.00, "lon": 35.42, "tip": "us", "detay": "NATO/ABD Stratejik Üssü"},
    {"isim": "Tartus Deniz Üssü (Suriye)", "lat": 34.91, "lon": 35.88, "tip": "us", "detay": "Rusya ve İran İkmal Noktası"},

    # --- İSRAİL SALDIRILARI (TURUNCU, İRAN'A VE VEKİLLERİNE) ---
    {"isim": "Şam Konsolosluğu Saldırısı", "lat": 33.51, "lon": 36.27, "tip": "israil", "detay": "İranlı Generaller Öldürüldü (1 Nisan 2024)"},
    {"isim": "İsfahan Radar Tesisi", "lat": 32.65, "lon": 51.66, "tip": "israil", "detay": "İran'a ilk doğrudan misilleme (19 Nisan 2024)"},
    {"isim": "Tahran Merkez - Suikast", "lat": 35.68, "lon": 51.38, "tip": "israil", "detay": "İsmail Haniye Suikastı (31 Temmuz 2024)"},
    {"isim": "Beyrut Dahiye Bombalaması", "lat": 33.85, "lon": 35.51, "tip": "israil", "detay": "Nasrallah ve Hizbullah Komutası (Eylül 2024)"},
    {"isim": "Hudeyde Limanı Bombalaması", "lat": 14.79, "lon": 42.95, "tip": "israil", "detay": "Husilere yönelik ağır bombardıman (Temmuz/Eylül 2024)"},
    {"isim": "Halep Silah Depoları", "lat": 36.20, "lon": 37.13, "tip": "israil", "detay": "Suriye içindeki İran ikmal hatları vuruldu"},
    {"isim": "Bekaa Vadisi", "lat": 34.00, "lon": 36.14, "tip": "israil", "detay": "Hizbullah mühimmat depoları operasyonları"},
    {"isim": "İran Misillemesi - Tahran Çevresi", "lat": 35.50, "lon": 51.10, "tip": "israil", "detay": "Ekim 2024 İsrail Geniş Çaplı Hava Harekatı"},
    {"isim": "İran Misillemesi - Huzistan", "lat": 31.32, "lon": 48.69, "tip": "israil", "detay": "Ekim 2024 Füze Tesisleri Hedefi"},
    {"isim": "İran Misillemesi - İlam", "lat": 33.63, "lon": 46.42, "tip": "israil", "detay": "Ekim 2024 Radar ve Savunma Sistemleri"},

    # --- İRAN SALDIRILARI (KIRMIZI, İSRAİL VE DİĞERLERİNE) ---
    {"isim": "Gerçek Vaat Operasyonu (Golan)", "lat": 33.01, "lon": 35.75, "tip": "iran", "detay": "Nisan 2024 İHA ve Füze Dalgaları"},
    {"isim": "Nevatim Üssü Balistik Saldırı", "lat": 31.21, "lon": 35.00, "tip": "iran", "detay": "Nisan ve Ekim 2024 Balistik Füze Hedefi"},
    {"isim": "Tel Aviv Mossad Yakını", "lat": 32.14, "lon": 34.82, "tip": "iran", "detay": "Ekim 2024 Balistik Füze Dalgaları"},
    {"isim": "Erbil Mossad İddiası", "lat": 36.19, "lon": 44.00, "tip": "iran", "detay": "Ocak 2024 Devrim Muhafızları Balistik Saldırısı"},
    {"isim": "Panjgur (Pakistan)", "lat": 26.97, "lon": 64.09, "tip": "iran", "detay": "Ocak 2024 Ceyşu'l Adl hedefleri"},
    {"isim": "Kızıldeniz Ticari Gemi Vurulması", "lat": 15.50, "lon": 41.50, "tip": "iran", "detay": "İran Destekli Husi Saldırıları (Sürekli)"},

    # --- ABD SALDIRILARI (MAVİ, İRAN VEKİLLERİNE) ---
    {"isim": "Sanaa (Yemen) Bombardımanı", "lat": 15.36, "lon": 44.19, "tip": "abd", "detay": "ABD ve İngiltere koalisyon saldırısı (Ocak/Şubat 2024)"},
    {"isim": "Al-Qaim (Irak)", "lat": 34.03, "lon": 41.14, "tip": "abd", "detay": "Ketaib Hizbullah tesisleri vuruldu (Şubat 2024)"},
    {"isim": "Akashat (Irak)", "lat": 33.38, "lon": 39.98, "tip": "abd", "detay": "İran bağlantılı milis lojistik merkezi"},
    {"isim": "Deyrizor (Suriye)", "lat": 35.33, "lon": 40.14, "tip": "abd", "detay": "İran Devrim Muhafızları depoları vuruldu"},
    {"isim": "Babil Milis Karargahı", "lat": 32.46, "lon": 44.40, "tip": "abd", "detay": "Irak direniş ekseni hedefleri"},
]

# Haritayı oluştur
m = folium.Map(location=[32.0, 45.0], zoom_start=5, tiles="CartoDB dark_matter")
m.get_root().html.add_child(folium.Element(pulse_css))

# İran Sınır Vurgusu
try:
    iran_geojson = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json"
    folium.GeoJson(iran_geojson, style_function=lambda x: {'fillColor': '#4a0000', 'color': '#ff0000', 'weight': 1, 'fillOpacity': 0.1}).add_to(m)
except: pass

# Noktaları haritaya yerleştirme
for olay in olaylar_ve_usler:
    if olay["tip"] == "us":
        icon_class = "icon-base"
        renk = "white"
    elif olay["tip"] == "israil":
        icon_class = "icon-israel-strike"
        renk = "orange"
    elif olay["tip"] == "iran":
        icon_class = "icon-iran-strike"
        renk = "red"
    elif olay["tip"] == "abd":
        icon_class = "icon-us-strike"
        renk = "cyan"
        
    tooltip_html = f"""
        <div style="font-family: Arial; color: white; background: #111; padding: 10px; border-radius: 5px; border: 1px solid {renk};">
            <b style="color:{renk};">📍 {olay['isim']}</b><br><hr style="margin:5px 0;">
            <b>Detay:</b> {olay['detay']}
        </div>
    """
    
    folium.Marker(
        location=[olay["lat"], olay["lon"]],
        tooltip=tooltip_html,
        icon=folium.DivIcon(html=f'<div class="{icon_class}"></div>')
    ).add_to(m)

st_folium(m, use_container_width=True, height=750)
