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
import json
import os

# --- SİSTEM AYARLARI ---
st.set_page_config(layout="wide", page_title="İran Savaş Monitörü", page_icon="⚔️", initial_sidebar_state="expanded")

# --- SESSION STATE (MANUEL VERİLER İÇİN) ---
# Gerçek bir veritabanı yerine basitlik için session_state kullanıyoruz. 
# Kalıcı olmasını isterseniz bir JSON dosyasına yazılabilir.
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = {
        "hurmuz": "AÇIK / GÜVENLİ",
        "polyester": 1250.0,
        "gubre": 480.0,
        "tr_5y_cds": 265.0,
        "avrupa_dgaz": 32.40,
        "jet_yakit": 85.20,
        "last_update": datetime.now().strftime('%H:%M:%S')
    }

# --- CSS / TAKTİKSEL İKONLAR ---
pulse_css = """
<style>
@keyframes pulse_red {0% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.6);} 50% {transform: scale(1.2); box-shadow: 0 0 0 6px rgba(255, 0, 0, 0);} 100% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);}}
@keyframes pulse_orange {0% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0.6);} 50% {transform: scale(1.2); box-shadow: 0 0 0 6px rgba(255, 165, 0, 0);} 100% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0);}}
@keyframes pulse_cyan {0% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.6);} 50% {transform: scale(1.2); box-shadow: 0 0 0 6px rgba(0, 255, 255, 0);} 100% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0);}}

.strike-ir {width: 12px; height: 12px; background-color: #ff0000; border-radius: 50%; border: 1.5px solid white; animation: pulse_red 2.5s infinite;}
.strike-il {width: 12px; height: 12px; background-color: #ff9900; border-radius: 50%; border: 1.5px solid white; animation: pulse_orange 2.5s infinite;}
.strike-us {width: 12px; height: 12px; background-color: #00ffff; border-radius: 50%; border: 1.5px solid white; animation: pulse_cyan 2.5s infinite;}

.stMetric { background: #1a1c1f; padding: 10px; border-radius: 5px; border-left: 3px solid #ff4b4b; }
</style>
"""
st.markdown(pulse_css, unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=30)
def get_live_data(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="2d")
        if h.empty: return 0.0, 0.0, 0.0
        c = h['Close'].iloc[-1]
        d = c - h['Close'].iloc[-2]
        p = (d / h['Close'].iloc[-2]) * 100
        return c, d, p
    except: return 0.0, 0.0, 0.0

def jitter(val, amount=0.15): 
    return val + random.uniform(-amount, amount)

@st.cache_data(ttl=600)
def scrape_war_news():
    queries = ["İran+saldırı", "İsrail+füze", "ABD+operasyon", "Hürmüz+Boğazı+Haber"]
    found_strikes = []
    # (Buradaki geo_db ve haber çekme mantığını koruyoruz)
    geo_db = {
        "Tahran": [35.68, 51.38, "il"], "İsfahan": [32.65, 51.66, "il"], "Natanz": [33.97, 51.92, "il"],
        "Tel Aviv": [32.08, 34.78, "ir"], "Hayfa": [32.79, 34.98, "ir"], "Beyrut": [33.89, 35.50, "il"]
    }
    all_news = []
    for q in queries:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={q}&hl=tr&gl=TR&ceid=TR:tr")
        for entry in feed.entries[:10]:
            all_news.append({"title": entry.title, "link": entry.link, "date": entry.published})
    return all_news

# --- SİDEBAR: YÖNETİM VE HABERLER ---
with st.sidebar:
    st.title("🎛️ KONTROL PANELİ")
    
    # Şifre Girişi
    password = st.text_input("Yönetici Şifresi", type="password")
    if password == "isedes":
        st.success("Erişim Onaylandı")
        with st.expander("📝 VERİLERİ GÜNCELLE"):
            m_hurmuz = st.selectbox("Hürmüz Durumu", ["AÇIK / GÜVENLİ", "RİSKLİ", "KISMEN KAPALI", "KAPALI"], index=0)
            m_poly = st.number_input("Polyester ($/Ton)", value=st.session_state.manual_data["polyester"])
            m_gubre = st.number_input("Gübre ($/Ton)", value=st.session_state.manual_data["gubre"])
            m_cds = st.number_input("Türkiye 5Y CDS", value=st.session_state.manual_data["tr_5y_cds"])
            m_dgaz = st.number_input("Avrupa Doğal Gaz (€/MWh)", value=st.session_state.manual_data["avrupa_dgaz"])
            m_jet = st.number_input("Jet Yakıt ($/Bbl)", value=st.session_state.manual_data["jet_yakit"])
            
            if st.button("SİSTEMİ GÜNCELLE VE KAYDET"):
                st.session_state.manual_data.update({
                    "hurmuz": m_hurmuz, "polyester": m_poly, "gubre": m_gubre,
                    "tr_5y_cds": m_cds, "avrupa_dgaz": m_dgaz, "jet_yakit": m_jet,
                    "last_update": datetime.now().strftime('%H:%M:%S')
                })
                st.rerun()
    else:
        if password: st.error("Hatalı Şifre")

    st.divider()
    st.subheader("📰 CANLI HABER AKIŞI")
    news_items = scrape_war_news()
    for n in news_items[:15]:
        st.markdown(f"**•** [{n['title']}]({n['link']})")
        st.caption(f"⏱ {n['date']}")
        st.divider()

# --- ANA EKRAN ÜST VERİ PANELİ ---
st.title("🇮🇷 İRAN SAVAŞ MONİTÖRÜ")
st.caption(f"Son Otomatik Güncelleme: {datetime.now().strftime('%H:%M:%S')} | Manuel Veri Güncelleme: {st.session_state.manual_data['last_update']}")

# Veri Çekme
usd, _, _ = get_live_data("TRY=X")
gold, _, gp = get_live_data("GC=F")
silver, _, sp = get_live_data("SI=F")
brent_v, _, bp = get_live_data("BZ=F")
wti, _, _ = get_live_data("CL=F")
vix, _, vp = get_live_data("^VIX")
us10y, _, up10 = get_live_data("^TNX")
tr10y, _, _ = get_live_data("TUR") # Proxy
alum, _, ap = get_live_data("ALI=F")
bdry, _, bdp = get_live_data("BDRY")

# Satır 1
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Baltic Dry (Navlun)", f"{bdry:.0f}", f"{bdp:+.2f}%")
c2.metric("Brent Vadeli", f"${brent_v:.2f}", f"{bp:+.2f}%")
c3.metric("Brent Spot (Tahmini)", f"${brent_v - 0.4: .2f}")
c4.metric("Sıvı Hidrokarbon (WTI)", f"${wti:.2f}")
c5.metric("Avrupa Doğal Gaz", f"€{st.session_state.manual_data['avrupa_dgaz']}", "MANUEL")

# Satır 2
c6, c7, c8, c9, c10 = st.columns(5)
c6.metric("Jet Yakıt", f"${st.session_state.manual_data['jet_yakit']}", "MANUEL")
c7.metric("Alüminyum", f"${alum:.2f}", f"{ap:+.2f}%")
c8.metric("Polyester", f"${st.session_state.manual_data['polyester']}", "MANUEL")
c9.metric("Gübre", f"${st.session_state.manual_data['gubre']}", "MANUEL")
c10.metric("Altın Gram", f"₺{((gold/31.1)*usd):.2f}", f"{gp:+.2f}%")

# Satır 3
c11, c12, c13, c14, c15 = st.columns(5)
c11.metric("Gümüş Gram", f"₺{((silver/31.1)*usd):.2f}", f"{sp:+.2f}%")
c12.metric("VIX (Korku)", f"{vix:.2f}", f"{vp:+.2f}%")
c13.metric("ABD 10Y Tahvil", f"%{us10y:.2f}", f"{up10:+.2f}%")
c14.metric("Türkiye 5Y CDS", f"{st.session_state.manual_data['tr_5y_cds']:.1f}", "MANUEL")
c15.metric("Türkiye 10Y", f"${tr10y:.2f}", "AUTO")

st.info(f"🚀 **Hürmüz Boğazı Durumu:** {st.session_state.manual_data['hurmuz']}")

# --- HARİTA ---
st.divider()

def map_render():
    m = folium.Map(location=[32.0, 48.0], zoom_start=5, tiles="CartoDB dark_matter")
    # Sabit Olaylar (Kendi veritabanınızdan)
    sabit_olaylar = [
        {"isim": "Parchin Askeri Kompleksi", "lat": 35.53, "lon": 51.77, "actor": "il", "desc": "Füze Üretim Tesisi Vuruldu"},
        {"isim": "Nevatim Hava Üssü", "lat": 31.20, "lon": 35.01, "actor": "ir", "desc": "Balistik Füze İsabeti"},
        {"isim": "Hürmüz Boğazı Devriye", "lat": 26.56, "lon": 56.45, "actor": "ir", "desc": "Donanma Hareketliliği"}
    ]
    
    for olay in sabit_olaylar:
        cls = "strike-ir" if olay["actor"] == "ir" else "strike-il" if olay["actor"] == "il" else "strike-us"
        color = "red" if olay["actor"] == "ir" else "orange" if olay["actor"] == "il" else "cyan"
        
        popup_html = f"<div style='color:white; background:#111; padding:10px; border:1px solid {color};'><b>{olay['isim']}</b><br>{olay['desc']}</div>"
        
        folium.Marker(
            location=[olay["lat"], olay["lon"]],
            popup=folium.Popup(popup_html, max_width=200),
            icon=folium.DivIcon(html=f'<div class="{cls}"></div>')
        ).add_to(m)

    st_folium(m, use_container_width=True, height=600)

map_render()
