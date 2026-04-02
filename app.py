import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import requests
import time

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Taktiksel OSINT & Finans Terminali", page_icon="🎯")

# --- YAN MENÜ ---
st.sidebar.title("⚙️ Kontrol Paneli")
st.sidebar.info("Askeri harita karanlık temada tasarlandı. En iyi deneyim için Streamlit temasını (Ayarlar -> Theme) 'Dark' olarak seçebilirsiniz.")

st.sidebar.markdown("---")
st.sidebar.success("🟢 **Canlı Akış Aktif:** Sistem her 60 saniyede bir piyasa verilerini otomatik günceller. Müdahale gerektirmez.")

# --- ANA BAŞLIK ---
st.title("🎯 Taktiksel İstihbarat & Canlı Finans Terminali")
st.markdown("Bölgesel aktörlerin konumları, vurulan hedefler ve piyasaların anlık tepkisi.")
st.divider()

# --- SEKME YAPISI ---
tab1, tab2 = st.tabs(["🗺️ Taktiksel Operasyon Haritası", "📊 Canlı Piyasa Terminali"])

# --- TAB 1: ASKERİ HARİTA VE VURULAN HEDEFLER ---
with tab1:
    st.subheader("Bölgesel Güç Dağılımı ve Sıcak Çatışma Noktaları")
    
    m = folium.Map(location=[32.4279, 53.6880], zoom_start=5, tiles="CartoDB dark_matter")

    # İran Sınır Vurgusu
    try:
        iran_geojson = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json"
        folium.GeoJson(
            iran_geojson,
            style_function=lambda feature: {
                'fillColor': '#8b0000',
                'color': '#ff0000',
                'weight': 2,
                'fillOpacity': 0.25
            }
        ).add_to(m)
    except:
        pass

    # 1. STANDART ASKERİ UNSURLAR (Önceki gibi)
    taktik_veriler = [
        {"isim": "İran Füze Üssü", "enlem": 35.68, "boylam": 51.38, "etiket": "IR", "renk": "white"},
        {"isim": "ABD Üssü (Irak)", "enlem": 33.31, "boylam": 44.36, "etiket": "US", "renk": "gray"},
        {"isim": "İsrail Unsurları", "enlem": 31.04, "boylam": 34.85, "etiket": "IL", "renk": "white"},
    ]

    for nokta in taktik_veriler:
        html_icon = f"""
            <div style="font-size: 14px; font-weight: bold; color: {nokta['renk']}; text-shadow: 1px 1px 2px black;">
                {nokta['etiket']}
            </div>
        """
        folium.Marker(
            location=[nokta["enlem"], nokta["boylam"]],
            tooltip=nokta["isim"],
            icon=folium.DivIcon(html=html_icon)
        ).add_to(m)
        nokta_renk = "red" if nokta["etiket"] == "IR" else "cyan" if nokta["etiket"] == "US" else "orange"
        folium.CircleMarker(
            location=[nokta["enlem"], nokta["boylam"]], radius=3, color=nokta_renk, fill=True, fill_color=nokta_renk
        ).add_to(m)

    # 2. VURULAN HEDEFLER (Yanıp sönen CSS animasyonu ile)
    bombalanan_yerler = [
        {"isim": "İsfahan Askeri Havalimanı (Vuruldu)", "enlem": 32.65, "boylam": 51.66},
        {"isim": "Natanz Nükleer Tesisi Yakını (Şüpheli Patlama)", "enlem": 33.97, "boylam": 51.92},
        {"isim": "Tebriz Radar Üssü (Saldırı Raporu)", "enlem": 38.07, "boylam": 46.29},
        {"isim": "Şam Konsolosluğu (Geçmiş Saldırı)", "enlem": 33.51, "boylam": 36.29}
    ]

    # CSS Animasyonu (Pulse efekti)
    pulse_css = """
        <style>
        @keyframes pulse {
            0% { transform: scale(0.8); opacity: 1; }
            50% { transform: scale(1.5); opacity: 0.5; }
            100% { transform: scale(0.8); opacity: 1; }
        }
        .pulse-icon {
            width: 24px;
            height: 24px;
            background-color: rgba(255, 0, 0, 0.8);
            border-radius: 50%;
            border: 2px solid #ffcccc;
            box-shadow: 0 0 15px red;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            animation: pulse 1.5s infinite;
        }
        </style>
    """
    
    # Animasyonu sayfaya gömüyoruz
    m.get_root().html.add_child(folium.Element(pulse_css))

    for bomba in bombalanan_yerler:
        html_bomba = f"""<div class="pulse-icon">💥</div>"""
        folium.Marker(
            location=[bomba["enlem"], bomba["boylam"]],
            tooltip=f"<b style='color:red;'>{bomba['isim']}</b>",
            icon=folium.DivIcon(html=html_bomba)
        ).add_to(m)

    st_folium(m, width="100%", height=650)


# --- TAB 2: CANLI PİYASA TERMINALI (OTOMATİK YENİLENİR) ---
with tab2:
    st.subheader("Canlı Finansal Veriler (Günlük Değişim)")
    
    # Önbelleği (cache) 60 saniye tutuyoruz, sayfa yenilendiğinde yeni veriyi yfinance üzerinden çekecek.
    @st.cache_data(ttl=60) 
    def get_live_ticker_data(ticker_symbol):
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change_val = current_price - prev_price
                change_pct = (change_val / prev_price) * 100
                return current_price, change_val, change_pct
            return 0, 0, 0
        except:
            return 0, 0, 0

    def display_metrics(title, assets):
        st.markdown(f"#### {title}")
        cols = st.columns(len(assets))
        for i, (name, symbol, format_str) in enumerate(assets):
            price, change, pct = get_live_ticker_data(symbol)
            with cols[i]:
                st.metric(
                    label=name,
                    value=f"{price:{format_str}}",
                    delta=f"{change:{format_str}} ({pct:.2f}%)"
                )
        st.markdown("<br>", unsafe_allow_html=True)

    currencies = [("USD/TRY", "TRY=X", ".2f"), ("EUR/TRY", "EURTRY=X", ".2f"), ("GBP/TRY", "GBPTRY=X", ".2f"), ("CNY/TRY", "CNYTRY=X", ".2f")]
    display_metrics("💵 Döviz Kurları", currencies)

    commodities = [("Brent Petrol", "BZ=F", ".2f"), ("Altın (Ons)", "GC=F", ".2f"), ("Gümüş", "SI=F", ".3f"), ("Doğalgaz", "NG=F", ".3f")]
    display_metrics("🛢️ Stratejik Emtialar", commodities)

    crypto_indices = [("Bitcoin (BTC)", "BTC-USD", ".0f"), ("S&P 500", "^GSPC", ".0f"), ("VIX (Korku)", "^VIX", ".2f"), ("DXY (Dolar)", "DX-Y.NYB", ".2f")]
    display_metrics("📊 Kripto & Endeksler", crypto_indices)

# --- OTOMATİK YENİLEME DÖNGÜSÜ (BÜYÜ PUSULASI) ---
# Site 60 saniye bekler ve sonra kendini otomatik olarak baştan yukarıdan aşağıya tekrar çalıştırır.
time.sleep(60)
st.rerun()
