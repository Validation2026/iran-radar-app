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
from tradingview_ta import TA_Handler, Interval

# --- SİSTEM AYARLARI ---
st.set_page_config(layout="wide", page_title="İran Savaş Monitörü", page_icon="⚔️", initial_sidebar_state="expanded")

# --- SESSION STATE (MANUEL VERİLER VE DEĞİŞİM TAKİBİ İÇİN) ---
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = {
        "hurmuz": "AÇIK / GÜVENLİ",
        "prev_hurmuz": "AÇIK / GÜVENLİ",
        "polyester": 1250.0,
        "prev_polyester": 1250.0,
        "gubre": 480.0,
        "prev_gubre": 480.0,
        "tr_5y_cds": 265.0,
        "prev_tr_5y_cds": 265.0,
        "jet_yakit": 85.20,
        "prev_jet_yakit": 85.20,
        "last_update": datetime.now().strftime('%H:%M:%S')
    }
else:
    anahtarlar = ["jet_yakit", "polyester", "gubre", "tr_5y_cds", "hurmuz"]
    for k in anahtarlar:
        prev_k = f"prev_{k}"
        if prev_k not in st.session_state.manual_data:
            st.session_state.manual_data[prev_k] = st.session_state.manual_data.get(k)

# Yüzdelik değişim hesaplama fonksiyonu
def calc_delta(current, prev):
    if prev == 0: return 0.0
    return ((current - prev) / prev) * 100

# --- CSS / TAKTİKSEL İKONLAR VE OKUNABİLİRLİK ---
pulse_css = """
<style>
@keyframes pulse_red {0% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.6);} 50% {transform: scale(1.2); box-shadow: 0 0 0 6px rgba(255, 0, 0, 0);} 100% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);}}
@keyframes pulse_orange {0% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0.6);} 50% {transform: scale(1.2); box-shadow: 0 0 0 6px rgba(255, 165, 0, 0);} 100% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 165, 0, 0);}}
@keyframes pulse_cyan {0% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.6);} 50% {transform: scale(1.2); box-shadow: 0 0 0 6px rgba(0, 255, 255, 0);} 100% {transform: scale(0.9); box-shadow: 0 0 0 0 rgba(0, 255, 255, 0);}}

.strike-ir {width: 12px; height: 12px; background-color: #ff0000; border-radius: 50%; border: 1.5px solid white; animation: pulse_red 2.5s infinite;}
.strike-il {width: 12px; height: 12px; background-color: #ff9900; border-radius: 50%; border: 1.5px solid white; animation: pulse_orange 2.5s infinite;}
.strike-us {width: 12px; height: 12px; background-color: #00ffff; border-radius: 50%; border: 1.5px solid white; animation: pulse_cyan 2.5s infinite;}

[data-testid="stMetric"] { 
    background-color: #1e2126 !important; 
    padding: 15px !important; 
    border-radius: 8px !important; 
    border-left: 4px solid #ff4b4b !important; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
}
[data-testid="stMetricLabel"] { 
    color: #a0aab5 !important; 
    font-weight: 600 !important;
    font-size: 14px !important;
}
[data-testid="stMetricValue"] { 
    color: #ffffff !important; 
    font-weight: bold !important;
}
</style>
"""
st.markdown(pulse_css, unsafe_allow_html=True)

# --- TRADINGVIEW & YFINANCE VERİ ÇEKİCİ ---
@st.cache_data(ttl=60)
def get_market_data(tv_symbol, tv_screener, tv_exchange, yf_ticker):
    try:
        handler = TA_Handler(symbol=tv_symbol, screener=tv_screener, exchange=tv_exchange, interval=Interval.INTERVAL_1_DAY)
        ind = handler.get_analysis().indicators
        close_price = ind.get("close", 0.0)
        open_price = ind.get("open", close_price)
        if close_price and close_price > 0:
            change = close_price - open_price
            pct = (change / open_price) * 100 if open_price > 0 else 0.0
            return close_price, change, pct
    except Exception: pass
    
    try:
        t = yf.Ticker(yf_ticker)
        h = t.history(period="2d")
        if h.empty: return 0.0, 0.0, 0.0
        c = h['Close'].iloc[-1]
        d = c - h['Close'].iloc[-2]
        p = (d / h['Close'].iloc[-2]) * 100
        return c, d, p
    except: return 0.0, 0.0, 0.0

def jitter(val, amount=0.15): 
    return val + random.uniform(-amount, amount)

# --- GELİŞMİŞ HABER TARAYICI ---
@st.cache_data(ttl=600)
def scrape_war_news():
    queries = [
        "İran+saldırı", "İsrail+füze+vurdu", "ABD+hava+harekatı", 
        "İran+okul+vuruldu", "İran+sivil+bina", "İsrail+yerleşim", 
        "hastane+saldırı", "Lübnan+sivil+kayıp", "Şam+bina+vuruldu"
    ]
    found_strikes = []
    all_news_sidebar = []
    
    geo_db = {
        "Tahran": [35.68, 51.38, "il"], "İsfahan": [32.65, 51.66, "il"], "Natanz": [33.97, 51.92, "il"],
        "Tebriz": [38.07, 46.29, "il"], "Şiraz": [29.59, 52.58, "il"], "Buşehr": [28.92, 50.83, "il"],
        "Kerec": [35.83, 50.99, "il"], "Kum": [34.64, 50.87, "il"], "Ahvaz": [31.31, 48.67, "il"],
        "Kirmanşah": [34.31, 47.06, "il"], "Bender Abbas": [27.18, 56.28, "il"], "Parchin": [35.53, 51.77, "il"],
        "Meşhed": [36.26, 59.61, "il"], "Semnan": [35.58, 53.39, "il"], "Arak": [34.09, 49.68, "il"],
        "Çabahar": [25.28, 60.62, "il"], "Hemedan": [35.19, 48.65, "il"], "Yezd": [31.89, 54.35, "il"],
        
        "Tel Aviv": [32.08, 34.78, "ir"], "Hayfa": [32.79, 34.98, "ir"], "Eilat": [29.55, 34.95, "ir"],
        "Kudüs": [31.76, 35.21, "ir"], "Negev": [30.80, 34.84, "ir"], "Aşkelon": [31.66, 34.57, "ir"],
        "Aşdod": [31.80, 34.65, "ir"], "Safed": [32.96, 35.49, "ir"], "Netanya": [32.32, 34.85, "ir"],
        "Dimona": [31.07, 35.02, "ir"], "Meron": [32.99, 35.41, "ir"], "Golan": [33.01, 35.75, "ir"],
        
        "Beyrut": [33.89, 35.50, "il"], "Dahiye": [33.85, 35.51, "il"], "Baalbek": [34.00, 36.21, "il"],
        "Şam": [33.51, 36.29, "il"], "Halep": [36.20, 37.13, "il"], "Deyrizor": [35.33, 40.14, "us"],
        "Bağdat": [33.31, 44.36, "us"], "Erbil": [36.19, 44.00, "ir"], "Sanaa": [15.36, 44.19, "us"],
        "Hudeyde": [14.79, 42.95, "il"], "Hürmüz": [26.56, 56.45, "ir"]
    }

    for q in queries:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={q}+after:2026-02-27&hl=tr&gl=TR&ceid=TR:tr")
        for entry in feed.entries[:25]:
            if entry.title not in [n["title"] for n in all_news_sidebar]:
                all_news_sidebar.append({"title": entry.title, "link": entry.link, "date": entry.published})

            for city, info in geo_db.items():
                if city.lower() in entry.title.lower():
                    found_strikes.append({
                        "isim": f"🔴 SON DAKİKA: {city} (Sivil/Askeri)",
                        "lat": jitter(info[0]), "lon": jitter(info[1]),
                        "actor": info[2],
                        "desc": f"Kaynak: {entry.title}",
                        "link": entry.link 
                    })
                    break 
    return found_strikes, all_news_sidebar

# --- SİDEBAR: YÖNETİM VE HABERLER ---
haber_harita, haber_sidebar = scrape_war_news()

with st.sidebar:
    st.title("🎛️ KONTROL PANELİ")
    
    password = st.text_input("Yönetici Şifresi", type="password")
    if password == "isedes":
        st.success("Erişim Onaylandı")
        with st.expander("📝 MANUEL VERİLERİ GÜNCELLE", expanded=True):
            m_hurmuz = st.selectbox("Hürmüz Durumu", ["AÇIK / GÜVENLİ", "RİSKLİ", "KISMEN KAPALI", "KAPALI"], index=["AÇIK / GÜVENLİ", "RİSKLİ", "KISMEN KAPALI", "KAPALI"].index(st.session_state.manual_data["hurmuz"]))
            m_poly = st.number_input("Polyester ($/Ton)", value=st.session_state.manual_data["polyester"])
            m_gubre = st.number_input("Gübre ($/Ton)", value=st.session_state.manual_data["gubre"])
            m_cds = st.number_input("Türkiye 5Y CDS", value=st.session_state.manual_data["tr_5y_cds"])
            m_jet = st.number_input("Jet Yakıt ($/Bbl)", value=st.session_state.manual_data["jet_yakit"])
            
            if st.button("SİSTEMİ GÜNCELLE VE KAYDET"):
                st.session_state.manual_data["prev_hurmuz"] = st.session_state.manual_data["hurmuz"]
                st.session_state.manual_data["prev_polyester"] = st.session_state.manual_data["polyester"]
                st.session_state.manual_data["prev_gubre"] = st.session_state.manual_data["gubre"]
                st.session_state.manual_data["prev_tr_5y_cds"] = st.session_state.manual_data["tr_5y_cds"]
                st.session_state.manual_data["prev_jet_yakit"] = st.session_state.manual_data["jet_yakit"]
                
                st.session_state.manual_data.update({
                    "hurmuz": m_hurmuz, "polyester": m_poly, "gubre": m_gubre,
                    "tr_5y_cds": m_cds, "jet_yakit": m_jet,
                    "last_update": datetime.now().strftime('%H:%M:%S')
                })
                st.rerun()
    else:
        if password: st.error("Hatalı Şifre")

    st.divider()
    st.subheader("📰 CANLI HABER AKIŞI")
    for n in haber_sidebar[:20]:
        st.markdown(f"**•** [{n['title']}]({n['link']})")
        st.divider()

# --- ANA EKRAN ÜST VERİ PANELİ ---
st.title("🇮🇷 İRAN SAVAŞ MONİTÖRÜ")
st.caption(f"Son Otomatik Güncelleme: {datetime.now().strftime('%H:%M:%S')} | Manuel Veri Güncelleme: {st.session_state.manual_data['last_update']}")

# TRADINGVIEW / YFINANCE VERİ ÇEKİMİ
usd_try, _, _ = get_market_data("USDTRY", "forex", "FX_IDC", "TRY=X")
gold_oz, _, gp = get_market_data("XAUUSD", "forex", "FX_IDC", "GC=F")
silver_oz, _, sp = get_market_data("XAGUSD", "forex", "FX_IDC", "SI=F")
brent_v, _, bp = get_market_data("UKOIL", "cfd", "TVC", "BZ=F")
wti, _, _ = get_market_data("USOIL", "cfd", "TVC", "CL=F")
ttf_gas, _, ttf_p = get_market_data("TTF1!", "cfd", "ICEEUR", "TTF=F") 
uranium, _, ura_p = get_market_data("UX1!", "cfd", "CME", "UX=F") 
vix, _, vp = get_market_data("VIX", "america", "CBOE", "^VIX")
us10y, _, up10 = get_market_data("US10Y", "cfd", "TVC", "^TNX")
tr10y, _, _ = get_market_data("TR10Y", "cfd", "TVC", "TUR")
alum, _, ap = get_market_data("ALUMINIUM", "cfd", "TVC", "ALI=F")
bdry, _, bdp = get_market_data("BDI", "index", "TVC", "BDRY")

# Altın/Gümüş Gram Hesaplama
gram_altin = (gold_oz / 31.1035) * usd_try if usd_try > 0 else 0
gram_gumus = (silver_oz / 31.1035) * usd_try if usd_try > 0 else 0

# Manuel Veriler İçin Değişim Hesaplamaları
d_jet = calc_delta(st.session_state.manual_data['jet_yakit'], st.session_state.manual_data['prev_jet_yakit'])
d_poly = calc_delta(st.session_state.manual_data['polyester'], st.session_state.manual_data['prev_polyester'])
d_gubre = calc_delta(st.session_state.manual_data['gubre'], st.session_state.manual_data['prev_gubre'])
d_cds = calc_delta(st.session_state.manual_data['tr_5y_cds'], st.session_state.manual_data['prev_tr_5y_cds'])

# KARTLAR İÇİN 4x4 DÜZEN
c1, c2, c3, c4 = st.columns(4)
c1.metric("Brent Vadeli", f"${brent_v:.2f}", f"{bp:+.2f}%")
c2.metric("Brent Spot (Tahmini)", f"${brent_v - 0.4: .2f}")
c3.metric("Sıvı Hidrok. (WTI)", f"${wti:.2f}")
c4.metric("Avrupa Doğal Gaz", f"€{ttf_gas:.2f}", f"{ttf_p:+.2f}%" if ttf_gas > 0 else "Veri Çekiliyor...")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Altın Gram", f"₺{gram_altin:.2f}", f"{gp:+.2f}%")
c6.metric("Gümüş Gram", f"₺{gram_gumus:.2f}", f"{sp:+.2f}%")
c7.metric("Alüminyum", f"${alum:.2f}", f"{ap:+.2f}%")
c8.metric("Uranyum", f"${uranium:.2f}", f"{ura_p:+.2f}%" if uranium > 0 else "Veri Çekiliyor...")

c9, c10, c11, c12 = st.columns(4)
c9.metric("Baltic Dry (Navlun)", f"{bdry:.0f}", f"{bdp:+.2f}%")
c10.metric("VIX (Korku)", f"{vix:.2f}", f"{vp:+.2f}%")
c11.metric("ABD 10Y Tahvil", f"%{us10y:.2f}", f"{up10:+.2f}%")
c12.metric("Türkiye 10Y", f"${tr10y:.2f}", "AUTO")

c13, c14, c15, c16 = st.columns(4)
c13.metric("Jet Yakıt", f"${st.session_state.manual_data['jet_yakit']}", f"{d_jet:+.2f}% (Mnl)")
c14.metric("Polyester", f"${st.session_state.manual_data['polyester']}", f"{d_poly:+.2f}% (Mnl)")
c15.metric("Gübre", f"${st.session_state.manual_data['gubre']}", f"{d_gubre:+.2f}% (Mnl)")
c16.metric("Türkiye 5Y CDS", f"{st.session_state.manual_data['tr_5y_cds']:.1f}", f"{d_cds:+.2f}% (Mnl)")

# Hürmüz Durumu Bildirimi
hurmuz_renk = "blue" if "AÇIK" in st.session_state.manual_data['hurmuz'] else "red" if "KAPALI" in st.session_state.manual_data['hurmuz'] else "orange"
st.markdown(f"""
<div style="padding: 15px; background-color: {hurmuz_renk}; color: white; border-radius: 8px; margin-top: 15px; margin-bottom: 15px; font-weight: bold; text-align: center; font-size: 18px;">
    🚀 HÜRMÜZ BOĞAZI DURUMU: {st.session_state.manual_data['hurmuz']}
</div>
""", unsafe_allow_html=True)


# --- HARİTA BAŞLIĞI VE LEJANT ---
st.divider()
st.markdown("""
### 🗺️ Stratejik Savaş ve Çatışma Haritası
**LEJANT:** 🔴 **Kırmızı:** İran Saldırıları/Operasyonları | 🟠 **Turuncu:** İsrail Saldırıları/Operasyonları | 🔵 **Mavi:** ABD Saldırıları/Operasyonları  
🛡️ **Gri Yıldız:** Kritik Askeri Üsler ve Karargahlar
""")

# --- HARİTA ---
@st.fragment(run_every="600s")
def map_render():
    m = folium.Map(location=[32.0, 48.0], zoom_start=5, tiles="CartoDB dark_matter")
    m.get_root().html.add_child(folium.Element(pulse_css))

    # İRAN SINIRLARINI ÇİZ (GeoJSON)
    try:
        iran_geojson = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json"
        folium.GeoJson(
            iran_geojson,
            style_function=lambda x: {'fillColor': '#ff0000', 'color': '#ff0000', 'weight': 2, 'fillOpacity': 0.05}
        ).add_to(m)
    except:
        pass

    # ASKERİ ÜSLER
    askeri_usler = [
        {"isim": "5. Filo Karargahı (ABD)", "lat": 26.20, "lon": 50.60, "ulke": "ABD"},
        {"isim": "Al Udeid Hava Üssü (ABD)", "lat": 25.11, "lon": 51.31, "ulke": "ABD"},
        {"isim": "Al Asad Hava Üssü (ABD)", "lat": 33.79, "lon": 42.43, "ulke": "ABD"},
        {"isim": "Nevatim Hava Üssü (İsrail)", "lat": 31.20, "lon": 35.01, "ulke": "İsrail"},
        {"isim": "Hatzerim Hava Üssü (İsrail)", "lat": 31.23, "lon": 34.66, "ulke": "İsrail"},
        {"isim": "Hayfa Deniz Üssü (İsrail)", "lat": 32.82, "lon": 34.98, "ulke": "İsrail"},
        {"isim": "İsfahan 8. Taktik Hava Üssü (İran)", "lat": 32.74, "lon": 51.86, "ulke": "İran"},
        {"isim": "Bender Abbas Deniz Üssü (İran)", "lat": 27.15, "lon": 56.19, "ulke": "İran"},
        {"isim": "Hamedan Nojeh Hava Üssü (İran)", "lat": 35.20, "lon": 48.65, "ulke": "İran"}
    ]

    for us in askeri_usler:
        popup_us_html = f"<div style='color:black; font-weight:bold;'>🛡️ {us['isim']}</div>"
        folium.Marker(
            location=[us["lat"], us["lon"]],
            tooltip=us["isim"],
            popup=folium.Popup(popup_us_html, max_width=200),
            icon=folium.Icon(color='lightgray', icon='star')
        ).add_to(m)

    # SALDIRI VE OLAYLAR
    sabit_olaylar = [
        {"isim": "Parchin Askeri Kompleksi", "lat": 35.53, "lon": 51.77, "actor": "il", "desc": "Tahran Yakını Füze Üretim Tesisi Vuruldu"},
        {"isim": "İsfahan Radar Sistemi", "lat": 32.65, "lon": 51.66, "actor": "il", "desc": "S-300 Bataryaları İmha Edildi"},
        {"isim": "Natanz Nükleer Tesisi Çevresi", "lat": 33.97, "lon": 51.92, "actor": "il", "desc": "Hava Savunma Hatlarına Önleyici Vuruş"},
        {"isim": "Bandar Abbas Limanı", "lat": 27.18, "lon": 56.28, "actor": "il", "desc": "İran Donanması Hızlı Hücumbotları Vuruldu"},
        {"isim": "Tebriz Füze Siloları", "lat": 38.07, "lon": 46.29, "actor": "il", "desc": "Yeraltı Silolarına F-35 Operasyonu"},
        {"isim": "Semnan Uzay ve Füze Merkezi", "lat": 35.58, "lon": 53.39, "actor": "il", "desc": "Balistik Füze Fırlatma Rampaları Vuruldu"},
        {"isim": "Meşhed Hava Üssü Çevresi", "lat": 36.26, "lon": 59.61, "actor": "il", "desc": "Erken Uyarı Radarları Etkisiz Hale Getirildi"},
        {"isim": "Ahvaz Petrol Altyapısı", "lat": 31.31, "lon": 48.67, "actor": "il", "desc": "Güneydeki Kritik Rafinerilerde Hasar Bildirildi"},
        {"isim": "Beyrut Dahiye Merkez", "lat": 33.85, "lon": 35.51, "actor": "il", "desc": "Hizbullah Üst Düzey Komuta Merkezi Vuruldu"},
        {"isim": "Hudeyde Limanı (Yemen)", "lat": 14.79, "lon": 42.95, "actor": "il", "desc": "Husi Petrol Depoları İsrail F-15'lerince Vuruldu"},
        {"isim": "Nevatim Hava Üssü", "lat": 31.20, "lon": 35.01, "actor": "ir", "desc": "Balistik Füze Yağmuru - Pistlerde Hasar"},
        {"isim": "Ramon Hava Üssü", "lat": 30.77, "lon": 34.67, "actor": "ir", "desc": "Fettah Hipersonik Füzeleri Hedef Aldı"},
        {"isim": "Meron Hava Kontrol Üssü", "lat": 32.99, "lon": 35.41, "actor": "ir", "desc": "Hizbullah Anti-Tank Füzeleriyle Radar Vurdu"},
        {"isim": "Tel Aviv (Kuzey Banliyöleri)", "lat": 32.11, "lon": 34.80, "actor": "ir", "desc": "Demir Kubbe'yi aşan füzeler sivil binalara isabet etti"},
        {"isim": "Erbil ABD Konsolosluğu Yakını", "lat": 36.23, "lon": 44.01, "actor": "ir", "desc": "Mossad Karargahı İddiasıyla Balistik Atış"},
        {"isim": "Sanaa Yeraltı Depoları", "lat": 15.36, "lon": 44.19, "actor": "us", "desc": "B-2 Spirit Bombardıman Uçakları Vurdu"}
    ]

    tum_olaylar = sabit_olaylar + haber_harita
    
    for olay in tum_olaylar:
        cls = "strike-ir" if olay["actor"] == "ir" else "strike-il" if olay["actor"] == "il" else "strike-us"
        border = "red" if olay["actor"] == "ir" else "orange" if olay["actor"] == "il" else "cyan"
        
        lat_final = olay["lat"]
        lon_final = olay["lon"]

        arama_sorgusu = urllib.parse.quote_plus(olay.get('isim', '') + " haberi")
        haber_linki = olay.get('link', f"https://news.google.com/search?q={arama_sorgusu}&hl=tr&gl=TR&ceid=TR:tr")

        popup_html = f"""
            <div style='color:white; background:#111; padding:12px; border-radius:6px; border:1px solid {border}; width:220px;'>
                <b style='color:{border}; font-size:14px;'>📍 {olay.get('isim', 'SALDIRI NOKTASI')}</b><br>
                <hr style='margin:6px 0; border-color:#333;'>
                <span style='font-size:12px; color:#ddd;'>{olay.get('desc', '')}</span><br>
                <a href='{haber_linki}' target='_blank' style='display:inline-block; margin-top:10px; color:#fff; background-color:{border}; text-decoration:none; font-size:11px; padding:4px 8px; border-radius:4px; font-weight:bold;'>🔗 HABERE GİT</a>
            </div>
        """
        
        folium.Marker(
            location=[lat_final, lon_final],
            tooltip=olay.get("isim", "Detay"),
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.DivIcon(html=f'<div class="{cls}"></div>')
        ).add_to(m)

    st_folium(m, use_container_width=True, height=750, key="war_map_2026", returned_objects=[])

map_render()
