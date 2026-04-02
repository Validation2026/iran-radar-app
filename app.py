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

# --- VERİ ÇEKME FONKSİYONLARI (CACHE SİSTEMİ) ---

# Finansal Veriler (60 Saniyede Bir Güncellenir)
@st.cache_data(ttl=60)
def get_finance_data(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="5d")
        if len(h) >= 2:
            close = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2]
            return close, close - prev, ((close - prev) / prev) * 100
        return 0, 0, 0
    except:
        return 0, 0, 0

# OSINT Canlı Haber Tarayıcı (600 Saniye / 10 Dakikada Bir Güncellenir)
@st.cache_data(ttl=600)
def fetch_live_osint():
    feed_url = "https://news.google.com/rss/search?q=saldırı+OR+füze+OR+patlama+OR+hava+savunma+İran+İsrail+ABD&hl=tr&gl=TR&ceid=TR:tr"
    feed = feedparser.parse(feed_url)
    
    # Stratejik Noktalar Sözlüğü (Haberde geçerse haritaya eklenecek)
    stratejik_noktalar = {
        "Tahran": (35.68, 51.38), "İsfahan": (32.65, 51.66), "Tebriz": (38.07, 46.29),
        "Şam": (33.51, 36.29), "Tel Aviv": (32.08, 34.78), "Kudüs": (31.76, 35.21),
        "Hayfa": (32.79, 34.98), "Negev": (30.80, 34.84), "Erbil": (36.19, 44.00),
        "Bağdat": (33.31, 44.36), "Kızıldeniz": (22.11, 38.59), "Hürmüz": (26.56, 56.45),
        "Beyrut": (33.89, 35.50), "Güney Lübnan": (33.27, 35.20), "Yemen": (15.55, 48.51)
    }
    
    canli_olaylar = []
    for item in feed.entries[:15]:
        for sehir, kordinat in stratejik_noktalar.items():
            if sehir.lower() in item.title.lower():
                canli_olaylar.append({
                    "isim": f"SON DAKİKA: {sehir} Bölgesi",
                    "lat": kordinat[0] + random.uniform(-0.1, 0.1), # Aynı noktada üst üste binmemesi için hafif sapma
                    "lon": kordinat[1] + random.uniform(-0.1, 0.1),
                    "tarih": "Canlı Teyit (Son 10 Dk)",
                    "kaynak": item.title,
                    "link": item.link,
                    "tip": "yeni"
                })
                break # Bir haber için bir lokasyon yeterli
    return canli_olaylar

# --- YAN MENÜ: CANLI FİNANS TERMINALI (SÜREKLİ GÜNCELLENİR) ---
st.sidebar.title("📟 CANLI TERMİNAL")
st.sidebar.caption(f"⏱️ Son Yenilenme: {datetime.now().strftime('%H:%M:%S')} (Otomatik)")
st.sidebar.divider()

# Altın/Gümüş Gram Hesaplaması İçin Dolar Kuru
usd_fiyat, usd_degisim, usd_pct = get_finance_data("TRY=X")
gold_ons, _, _ = get_finance_data("GC=F")
silver_ons, _, _ = get_finance_data("SI=F")
gram_altin = (gold_ons / 31.1035) * usd_fiyat if usd_fiyat > 0 else 0
gram_gumus = (silver_ons / 31.1035) * usd_fiyat if usd_fiyat > 0 else 0

def sidebar_metric(label, symbol, formatter="${:.2f}"):
    c, d, p = get_finance_data(symbol)
    st.sidebar.metric(label, formatter.format(c), f"{d:+.2f} ({p:+.2f}%)")

with st.sidebar.expander("🛢️ ENERJİ & NAVLUN", expanded=True):
    sidebar_metric("Brent Vadeli", "BZ=F")
    sidebar_metric("Brent Spot (Proxy)", "BNO") # Gerçek spot verisi değişkendir, ETF proxy kullanılır
    sidebar_metric("Sıvı Hidrokarbon (WTI)", "CL=F")
    sidebar_metric("Avrupa Doğalgaz (TTF)", "TTF=F", "€{:.2f}")
    sidebar_metric("Jet Yakıtı (Proxy)", "HO=F")
    sidebar_metric("Baltic Dry (BDRY)", "BDRY", "{:.2f}")

with st.sidebar.expander("🚢 HÜRMÜZ TRAFİĞİ (Simüle)", expanded=True):
    # Bu veriler API'ler ücretli olduğu için rastgele dalgalanan canlı simülasyonlardır
    bati_tanker = 14 + random.randint(-2, 2)
    dogu_tanker = 11 + random.randint(-2, 2)
    st.sidebar.metric("⬅️ Batıya Giden Tanker", bati_tanker, random.randint(-1, 1))
    st.sidebar.metric("➡️ Doğuya Giden Tanker", dogu_tanker, random.randint(-1, 1))

with st.sidebar.expander("🏗️ ENDÜSTRİYEL & TARIM", expanded=False):
    sidebar_metric("Alüminyum", "ALI=F")
    sidebar_metric("Gübre (CF Ind.)", "CF")
    sidebar_metric("Polyester (Celanese)", "CE")

with st.sidebar.expander("💰 METALLER & DÖVİZ", expanded=False):
    st.sidebar.metric("Altın Gram", f"₺{gram_altin:.2f}")
    st.sidebar.metric("Gümüş Gram", f"₺{gram_gumus:.2f}")
    sidebar_metric("USD/TRY", "TRY=X", "₺{:.4f}")

with st.sidebar.expander("🏛️ RİSK & TAHVİL", expanded=True):
    sidebar_metric("VIX (Korku Endeksi)", "^VIX", "{:.2f}")
    sidebar_metric("ABD 10Y Tahvil", "^TNX", "%{:.2f}")
    sidebar_metric("TR 10Y (TUR Proxy)", "TUR", "${:.2f}")
    st.sidebar.metric("Türkiye CDS (Simüle)", f"{265.4 + random.uniform(-3, 3):.1f}", "Canlı")

# --- ANA EKRAN: OSINT HARİTASI ---
st.title("🗺️ Taktiksel İstihbarat ve Operasyon Haritası")
st.caption("Bu harita 10 dakikada bir küresel istihbarat ağlarını tarayarak yeni çatışma noktalarını otomatik olarak ekler.")

# Harita Altyapısı
m = folium.Map(location=[32.0, 45.0], zoom_start=5, tiles="CartoDB dark_matter")

# Tarihsel Veriler (Çatışmanın Başından Beri)
tarihsel_olaylar = [
    {"isim": "İsrail Şam Konsolosluğu Saldırısı", "lat": 33.51, "lon": 36.29, "tarih": "1 Nisan 2024", "kaynak": "Tarihsel Kayıt", "tip": "eski"},
    {"isim": "Gerçek Vaat Operasyonu (Negev Üssü)", "lat": 30.80, "lon": 34.84, "tarih": "13-14 Nisan 2024", "kaynak": "Tarihsel Kayıt", "tip": "eski"},
    {"isim": "İsfahan Hava Üssü Misillemesi", "lat": 32.65, "lon": 51.66, "tarih": "19 Nisan 2024", "kaynak": "Tarihsel Kayıt", "tip": "eski"},
    {"isim": "Kızıldeniz Husiler Gemi Vurulması", "lat": 15.0, "lon": 42.0, "tarih": "2023 Sonu - Devam Ediyor", "kaynak": "CENTCOM", "tip": "eski"},
    {"isim": "Beyrut Güney Banliyö Saldırıları", "lat": 33.85, "lon": 35.51, "tarih": "Eylül 2024", "kaynak": "Tarihsel Kayıt", "tip": "eski"},
    {"isim": "İran 2. Balistik Füze Dalgası (Nevatim)", "lat": 31.20, "lon": 35.01, "tarih": "Ekim 2024", "kaynak": "Tarihsel Kayıt", "tip": "eski"},
]

# Canlı Taranan Olayları Çek
canli_olaylar = fetch_live_osint()
tum_olaylar = tarihsel_olaylar + canli_olaylar

# Animasyon CSS
pulse_css = """
<style>
@keyframes pulse_red {0% {transform: scale(0.9); opacity: 1;} 50% {transform: scale(1.5); opacity: 0.6;} 100% {transform: scale(0.9); opacity: 1;}}
@keyframes pulse_orange {0% {transform: scale(0.9); opacity: 1;} 50% {transform: scale(1.2); opacity: 0.8;} 100% {transform: scale(0.9); opacity: 1;}}
.icon-yeni {width: 25px; height: 25px; background-color: rgba(255, 0, 0, 0.9); border-radius: 50%; border: 2px solid white; box-shadow: 0 0 15px red; animation: pulse_red 1s infinite;}
.icon-eski {width: 15px; height: 15px; background-color: rgba(255, 165, 0, 0.7); border-radius: 50%; border: 1px solid white; animation: pulse_orange 2.5s infinite;}
</style>
"""
m.get_root().html.add_child(folium.Element(pulse_css))

# İşaretçileri Haritaya Ekleme
for b in tum_olaylar:
    icon_class = "icon-yeni" if b["tip"] == "yeni" else "icon-eski"
    border_color = "red" if b["tip"] == "yeni" else "orange"
    
    tooltip_html = f"""
        <div style="font-family: Arial; color: white; background: #111; padding: 10px; border-radius: 5px; border: 1px solid {border_color}; min-width: 200px;">
            <b style="color:{border_color};">📍 {b['isim']}</b><br><hr style="margin:5px 0;">
            📅 <b>Tarih:</b> {b['tarih']}<br>
            📡 <b>Kaynak:</b> {b['kaynak']}
        </div>
    """
    
    folium.Marker(
        location=[b["lat"], b["lon"]],
        tooltip=tooltip_html,
        icon=folium.DivIcon(html=f'<div class="{icon_class}"></div>')
    ).add_to(m)

st_folium(m, use_container_width=True, height=750)

# --- OTOMATİK YENİLEME DÖNGÜSÜ (60 Saniye) ---
# Site açık kaldığı sürece verileri her dakika günceller.
# Harita taraması ise cache (ttl=600) sayesinde 10 dakikada bir yeni veriye bakar.
time.sleep(60)
st.rerun()
