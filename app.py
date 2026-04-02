import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import time

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Stratejik Analiz & Piyasa Terminali", page_icon="📡")

# --- YAN MENÜ ---
st.sidebar.title("📡 Sistem Durumu")
st.sidebar.success("🟢 CANLI AKIŞ AKTİF")
st.sidebar.info("Veriler her 60 saniyede bir otomatik yenilenir. Haritadaki hedeflerin üzerine gelerek detayları görebilirsiniz.")
st.sidebar.markdown("---")
st.sidebar.write(f"Son Güncelleme: {time.strftime('%H:%M:%S')}")

# --- ANA BAŞLIK ---
st.title("🛡️ Taktiksel İstihbarat ve Küresel Emtia Terminali")
st.divider()

# --- SEKME YAPISI ---
tab1, tab2 = st.tabs(["🗺️ Detaylı Operasyon Haritası", "📟 Canlı Veri Terminali"])

# --- TAB 1: DETAYLI HARİTA ---
with tab1:
    st.subheader("Bölgesel Saldırı ve Operasyon Detayları")
    
    m = folium.Map(location=[32.0, 53.0], zoom_start=5, tiles="CartoDB dark_matter")

    # İran Sınır Vurgusu
    try:
        iran_geojson = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json"
        folium.GeoJson(iran_geojson, style_function=lambda x: {'fillColor': '#8b0000', 'color': '#ff0000', 'weight': 1, 'fillOpacity': 0.1}).add_to(m)
    except: pass

    # Genişletilmiş Bombalanan Yerler Verisi
    bombalanan_yerler = [
        {"isim": "İsfahan Hava Üssü", "lat": 32.65, "lon": 51.66, "tarih": "19 Nisan 2024", "kaynak": "ABC News / OSINT"},
        {"isim": "Natanz Nükleer Tesisi", "lat": 33.97, "lon": 51.92, "tarih": "Sürekli Tehdit", "kaynak": "IAEA Raporları"},
        {"isim": "Tebriz Radar İstasyonu", "lat": 38.07, "lon": 46.29, "tarih": "19 Nisan 2024", "kaynak": "Yerel Kaynaklar"},
        {"isim": "Bandar Abbas Donanma Üssü", "lat": 27.18, "lon": 56.28, "tarih": "Gerginlik Artışı", "kaynak": "Uydu Görüntüleri"},
        {"isim": "Kharg Adası Petrol Terminali", "lat": 29.23, "lon": 50.31, "tarih": "Siber Saldırı / Tehdit", "kaynak": "Enerji Bakanlığı"},
        {"isim": "Ahvaz Lojistik Merkezi", "lat": 31.31, "lon": 48.67, "tarih": "Patlama Raporu", "kaynak": "Telegram OSINT"},
        {"isim": "Kermanshah İHA Üssü", "lat": 34.34, "lon": 47.15, "tarih": "Hava Hareketliliği", "kaynak": "Sınır Gözlem"},
        {"isim": "Şiraz Hava Savunma Hattı", "lat": 29.54, "lon": 52.58, "tarih": "Aktif Çatışma", "kaynak": "Sosyal Medya Teyitli"},
        {"isim": "Hürmüz Boğazı Devriye Hattı", "lat": 26.56, "lon": 56.45, "tarih": "Gemilere El Koyma", "kaynak": "Lloyd's List"}
    ]

    # Pulse CSS
    pulse_css = """<style>@keyframes pulse {0% {transform: scale(0.9); opacity: 1;} 50% {transform: scale(1.4); opacity: 0.6;} 100% {transform: scale(0.9); opacity: 1;}}
    .pulse-icon {width: 20px; height: 20px; background-color: rgba(255, 0, 0, 0.8); border-radius: 50%; border: 1px solid white; box-shadow: 0 0 10px red; animation: pulse 1.5s infinite;}</style>"""
    m.get_root().html.add_child(folium.Element(pulse_css))

    for b in bombalanan_yerler:
        # Tooltip içeriği: Üstüne gelince görünen bilgi
        tooltip_content = f"""
            <div style="font-family: sans-serif; color: white; background: #222; padding: 10px; border-radius: 5px; border: 1px solid red;">
                <b>📍 {b['isim']}</b><br>
                📅 Tarih: {b['tarih']}<br>
                📡 Kaynak: {b['kaynak']}
            </div>
        """
        folium.Marker(
            location=[b["lat"], b["lon"]],
            tooltip=tooltip_content,
            icon=folium.DivIcon(html='<div class="pulse-icon"></div>')
        ).add_to(m)

    st_folium(m, width="100%", height=600)

# --- TAB 2: DEVASA VERİ TERMİNALİ ---
with tab2:
    @st.cache_data(ttl=60)
    def get_data(ticker):
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="2d")
            return h['Close'].iloc[-1], h['Close'].iloc[-1] - h['Close'].iloc[-2]
        except: return 0, 0

    # Gram Altın/Gümüş Hesaplama (Ons / 31.1035 * USDTRY)
    usd_try, _ = get_data("TRY=X")
    gold_ons, gold_chg = get_data("GC=F")
    silver_ons, silver_chg = get_data("SI=F")
    
    gram_altin = (gold_ons / 31.1035) * usd_try if usd_try > 0 else 0
    gram_gumus = (silver_ons / 31.1035) * usd_try if usd_try > 0 else 0

    # Kategorize Edilmiş Veriler
    st.subheader("🛢️ Enerji ve Navlun (Hürmüz & Global)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Brent Vadeli (BZ=F)", f"${get_data('BZ=F')[0]:.2f}", f"{get_data('BZ=F')[1]:.2f}")
    with c2: st.metric("Baltic Dry (BDRY)", f"{get_data('BDRY')[0]:.2f}", f"{get_data('BDRY')[1]:.2f}%")
    with c3: st.metric("Avrupa Doğalgaz (TTF)", f"€{get_data('TTF=F')[0]:.2f}", f"{get_data('TTF=F')[1]:.2f}")
    with c4: st.metric("Jet Yakıt (Proxy: HO=F)", f"${get_data('HO=F')[0]:.2f}", f"{get_data('HO=F')[1]:.2f}")

    st.markdown("---")
    st.subheader("🏗️ Endüstriyel Emtia ve Tarım")
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.metric("Alüminyum", f"${get_data('ALI=F')[0]:.2f}", f"{get_data('ALI=F')[1]:.2f}")
    with c6: st.metric("Gübre (CF Ind.)", f"${get_data('CF')[0]:.2f}", f"{get_data('CF')[1]:.2f}")
    with c7: st.metric("Polyester (Proxy: PX)", f"${get_data('CE')[0]:.2f}", f"{get_data('CE')[1]:.2f}") # Celanese Corp proxy
    with c8: st.metric("Sıvı Hidrokarbon", f"${get_data('CL=F')[0]:.2f}", f"{get_data('CL=F')[1]:.2f}")

    st.markdown("---")
    st.subheader("💰 Değerli Metaller (Gram/TRY)")
    c9, c10, c11, c12 = st.columns(4)
    with c9: st.metric("Altın Gram", f"₺{gram_altin:.2f}")
    with c10: st.metric("Gümüş Gram", f"₺{gram_gumus:.2f}")
    with c11: st.metric("VIX (Korku)", f"{get_data('^VIX')[0]:.2f}", f"{get_data('^VIX')[1]:.2f}%")
    with c12: st.metric("USD/TRY", f"₺{usd_try:.4f}")

    st.markdown("---")
    st.subheader("🏛️ Tahviller ve Risk (CDS)")
    c13, c14, c15, c16 = st.columns(4)
    with c13: st.metric("ABD 10Y Tahvil", f"%{get_data('^TNX')[0]:.2f}", f"{get_data('^TNX')[1]:.2f}")
    with c14: st.metric("TR 10Y (Proxy: TUR)", f"{get_data('TUR')[0]:.2f}", f"{get_data('TUR')[1]:.2f}")
    with c15: st.metric("Hürmüz Gemi Trafiği", "AKTİF", "Normal") # Statik/Simüle
    with c16: st.metric("Türkiye CDS (Simüle)", "265.4", "-2.1") # CDS doğrudan yfinance'de yoktur

    # Tanker Verileri İçin Özel Panel
    st.markdown("---")
    st.subheader("🚢 Hürmüz Boğazı Tanker Takibi (Simüle Edilen Veri)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info("⬅️ **Batıya Giden Tanker Sayısı (Son 24s):** 14")
    with col_t2:
        st.info("➡️ **Doğuya Giden Tanker Sayısı (Son 24s):** 11")

# --- AUTO REFRESH SİSTEMİ ---
time.sleep(60)
st.rerun()
