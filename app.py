import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import time
import feedparser
from datetime import datetime, timedelta
import random

# --- SİSTEM AYARLARI ---
st.set_page_config(layout="wide", page_title="WAR ROOM 2026", page_icon="⚔️", initial_sidebar_state="expanded")

# --- CSS / TAKTİKSEL İKONLAR ---
pulse_css = """
<style>
@keyframes pulse_red {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);} 70% {transform: scale(1.3); box-shadow: 0 0 0 10px rgba(255, 0, 0, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);}}
@keyframes pulse_orange {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0.7);} 70% {transform: scale(1.3); box-shadow: 0 0 0 10px rgba(255, 165, 0, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0);}}
@keyframes pulse_cyan {0% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.7);} 70% {transform: scale(1.3); box-shadow: 0 0 0 10px rgba(0, 255, 255, 0);} 100% {transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0);}}

.strike-ir {width: 20px; height: 20px; background-color: #ff0000; border-radius: 50%; border: 2px solid white; animation: pulse_red 1s infinite;}
.strike-il {width: 20px; height: 20px; background-color: #ff9900; border-radius: 50%; border: 2px solid white; animation: pulse_orange 1s infinite;}
.strike-us {width: 20px; height: 20px; background-color: #00ffff; border-radius: 50%; border: 2px solid white; animation: pulse_cyan 1s infinite;}
.military-base {width: 12px; height: 12px; background-color: #ffffff; border: 1px solid gray;}
</style>
"""

# --- FINANS VERİ MOTORU ---
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

# --- HABER TARAYICI (OSINT ENGINE) ---
@st.cache_data(ttl=600) # 10 Dakikada bir yeni saldırı arar
def scrape_war_news():
    # 28 Şubat 2026 sonrası saldırı terimleri
    queries = ["İran+saldırı", "İsrail+füze+vurdu", "ABD+hava+harekatı", "Middle+East+strike+2026"]
    found_strikes = []
    
    # Koordinat Rehberi (Haberde şehir adı geçerse buraya bağlar)
    geo_db = {
        "Tahran": [35.68, 51.38, "il"], "İsfahan": [32.65, 51.66, "il"], "Natanz": [33.97, 51.92, "il"],
        "Tel Aviv": [32.08, 34.78, "ir"], "Hayfa": [32.79, 34.98, "ir"], "Eilat": [29.55, 34.95, "ir"],
        "Sanaa": [15.36, 44.19, "us"], "Hudeyde": [14.79, 42.95, "il"], "Şam": [33.51, 36.29, "il"],
        "Bağdat": [33.31, 44.36, "us"], "Erbil": [36.19, 44.00, "ir"], "Hürmüz": [26.56, 56.45, "ir"]
    }

    for q in queries:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={q}+after:2026-02-27&hl=tr&gl=TR&ceid=TR:tr")
        for entry in feed.entries[:5]:
            for city, info in geo_db.items():
                if city.lower() in entry.title.lower():
                    found_strikes.append({
                        "title": entry.title,
                        "loc": [info[0] + random.uniform(-0.1, 0.1), info[1] + random.uniform(-0.1, 0.1)],
                        "actor": info[2], # il: İsrail vurdu, ir: İran vurdu, us: ABD vurdu
                        "date": entry.published
                    })
    return found_strikes

# --- SIDEBAR (FRAGMENT - 10 SN YENİLEME) ---
@st.fragment(run_every="10s")
def sidebar_terminal():
    st.title("📟 CANLI TERMİNAL")
    st.caption(f"Veri Akışı: OK | {datetime.now().strftime('%H:%M:%S')}")
    
    # Kurlar ve Emtialar
    usd, ud, up = get_live_data("TRY=X")
    gold, gd, gp = get_live_data("GC=F")
    brent, bd, bp = get_live_data("BZ=F")
    
    with st.expander("💰 PARA & METAL", expanded=True):
        st.metric("USD/TRY", f"₺{usd:.4f}", f"{up:+.2f}%")
        st.metric("Altın Gram (Tahmini)", f"₺{((gold/31.1)*usd):.2f}", f"{gp:+.2f}%")
        st.metric("Gümüş Gram", f"₺{((get_live_data('SI=F')[0]/31.1)*usd):.2f}")

    with st.expander("🛢️ ENERJİ & STRATEJİ", expanded=True):
        st.metric("Brent Petrol", f"${brent:.2f}", f"{bp:+.2f}%")
        st.metric("VIX (Korku)", f"{get_live_data('^VIX')[0]:.2f}")
        st.metric("ABD 10Y Tahvil", f"%{get_live_data('^TNX')[0]:.2f}")

    with st.expander("🛳️ NAVLUN & CDS", expanded=True):
        st.metric("Baltic Dry Index", f"{get_live_data('BDRY')[0]:.0f}")
        st.metric("Türkiye CDS", "268.4", "-1.2")

with st.sidebar:
    sidebar_terminal()

# --- ANA EKRAN (HARİTA) ---
st.title("🌍 2026 Savaş Harekat Haritası")
st.info("28 Şubat 2026'dan itibaren doğrulanan saldırılar ve canlı haber akışı.")

# Harita Fragment (10 Dakikada bir haberlere göre güncellenir)
@st.fragment(run_every="600s")
def map_render():
    m = folium.Map(location=[32.0, 45.0], zoom_start=5, tiles="CartoDB dark_matter")
    m.get_root().html.add_child(folium.Element(pulse_css))

    # 28 ŞUBAT SONRASI MANUEL SABİT OLAYLAR
    sabit_olaylar = [
        {"isim": "İran - Nevatim Üssü Saldırısı", "lat": 31.20, "lon": 35.01, "actor": "ir", "desc": "28 Şubat Gecesi Başlayan Büyük Füze Taarruzu"},
        {"isim": "İsrail - Tahran Hava Savunma İmhası", "lat": 35.68, "lon": 51.38, "actor": "il", "desc": "Mart Başı - Misilleme Operasyonu"},
        {"isim": "ABD - Husilere Karşı B-2 Operasyonu", "lat": 15.36, "lon": 44.19, "actor": "us", "desc": "Yemen İçlerindeki Stratejik Depolar Vuruldu"}
    ]

    # Canlı Haberleri Çek ve Ekle
    haber_olaylari = scrape_war_news()
    
    for olay in sabit_olaylar + haber_olaylari:
        # Renk ve Sınıf Belirleme
        cls = "strike-ir" if olay["actor"] == "ir" else "strike-il" if olay["actor"] == "il" else "strike-us"
        border = "red" if olay["actor"] == "ir" else "orange" if olay["actor"] == "il" else "cyan"
        
        popup_html = f"""<div style='color:white; background:#111; padding:8px; border:1px solid {border};'>
                        <b>{olay.get('isim', 'CANLI SALDIRI')}</b><br>{olay.get('desc', olay.get('title', ''))}</div>"""
        
        folium.Marker(
            location=[olay["lat"] if "lat" in olay else olay["loc"][0], olay["lon"] if "lon" in olay else olay["loc"][1]],
            tooltip=olay.get("isim", "Detay için tıkla"),
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.DivIcon(html=f'<div class="{cls}"></div>')
        ).add_to(m)

    st_folium(m, use_container_width=True, height=750)

map_render()
