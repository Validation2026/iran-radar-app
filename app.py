import streamlit as st
import pandas as pd
import yfinance as yf
import folium
from streamlit_folium import st_folium
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Taktiksel OSINT & Finans Terminali", page_icon="🎯")

# --- YAN MENÜ ---
st.sidebar.title("⚙️ Kontrol Paneli")
st.sidebar.info("Askeri harita karanlık temada tasarlandı. En iyi deneyim için Streamlit temasını (Ayarlar -> Theme) 'Dark' olarak seçebilirsiniz.")

# Canlı yenileme butonu
if st.sidebar.button("🔄 Piyasa Verilerini Canlı Güncelle"):
    st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.markdown("**Veri Akışı:** Aktif 🟢")

# --- ANA BAŞLIK ---
st.title("🎯 Taktiksel İstihbarat & Canlı Finans Terminali")
st.markdown("Bölgesel aktörlerin (US, IL, IR) konumları ve piyasaların anlık tepkisi.")
st.divider()

# --- SEKME YAPISI ---
tab1, tab2 = st.tabs(["🗺️ Taktiksel Operasyon Haritası", "📊 Canlı Piyasa Terminali (TradingView Tarzı)"])

# --- TAB 1: GÖRSELDEKİ GİBİ ASKERİ HARİTA ---
with tab1:
    st.subheader("Bölgesel Güç Dağılımı ve Hedefler")
    
    # Karanlık Taktiksel Harita
    m = folium.Map(location=[32.4279, 53.6880], zoom_start=5, tiles="CartoDB dark_matter")

    # İran'ın sınırlarını kırmızı ile vurgulama (GeoJSON kullanarak)
    try:
        iran_geojson = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/IRN.geo.json"
        folium.GeoJson(
            iran_geojson,
            style_function=lambda feature: {
                'fillColor': '#8b0000', # Koyu Kırmızı
                'color': '#ff0000',     # Parlak Kırmızı Sınır
                'weight': 2,
                'fillOpacity': 0.25
            }
        ).add_to(m)
    except:
        pass # Eğer internetten çekemezse hata vermesin

    # Görseldeki gibi Metin Tabanlı (DivIcon) İşaretçiler
    taktik_veriler = [
        {"isim": "İran Füze Üssü", "enlem": 35.68, "boylam": 51.38, "etiket": "IR", "renk": "white"},
        {"isim": "ABD Üssü (Irak)", "enlem": 33.31, "boylam": 44.36, "etiket": "US", "renk": "gray"},
        {"isim": "İsrail Unsurları", "enlem": 31.04, "boylam": 34.85, "etiket": "IL", "renk": "white"},
        {"isim": "İran Donanması", "enlem": 27.18, "boylam": 56.02, "etiket": "IR", "renk": "white"},
        {"isim": "ABD Merkez Kuvvetler", "enlem": 25.27, "boylam": 51.53, "etiket": "US", "renk": "gray"},
        {"isim": "İsrail Hava Hedefi", "enlem": 32.70, "boylam": 35.30, "etiket": "IL", "renk": "white"},
    ]

    for nokta in taktik_veriler:
        # Askeri stilde CSS ile ikon oluşturma
        html_icon = f"""
            <div style="
                font-size: 14px; 
                font-weight: bold; 
                color: {nokta['renk']}; 
                text-shadow: 1px 1px 2px black;
                font-family: Arial, sans-serif;">
                {nokta['etiket']}
            </div>
        """
        
        folium.Marker(
            location=[nokta["enlem"], nokta["boylam"]],
            tooltip=nokta["isim"],
            icon=folium.DivIcon(html=html_icon)
        ).add_to(m)

        # Altlarına küçük kırmızı/mavi noktalar ekleyelim (Görseldeki detayı yakalamak için)
        nokta_renk = "red" if nokta["etiket"] == "IR" else "cyan" if nokta["etiket"] == "US" else "orange"
        folium.CircleMarker(
            location=[nokta["enlem"], nokta["boylam"]],
            radius=3, color=nokta_renk, fill=True, fill_color=nokta_renk
        ).add_to(m)

    st_folium(m, width="100%", height=650)


# --- TAB 2: CANLI PİYASA TERMINALI (SAYISAL DEĞERLER) ---
with tab2:
    st.subheader("Canlı Finansal Veriler (Günlük Değişim)")
    
    # Yfinance'den anlık fiyat ve günlük değişimi hesaplayan fonksiyon
    @st.cache_data(ttl=60) # Her 60 saniyede bir otomatik veriyi eskitir
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
                # Streamlit'in native metric aracı TradingView sayıları gibi görünür
                st.metric(
                    label=name,
                    value=f"{price:{format_str}}",
                    delta=f"{change:{format_str}} ({pct:.2f}%)"
                )
        st.markdown("<br>", unsafe_allow_html=True) # Boşluk

    # --- 1. DÖVİZLER ---
    currencies = [
        ("USD/TRY", "TRY=X", ".2f"),
        ("EUR/TRY", "EURTRY=X", ".2f"),
        ("GBP/TRY", "GBPTRY=X", ".2f"),
        ("CNY/TRY", "CNYTRY=X", ".2f")
    ]
    display_metrics("💵 Döviz Kurları", currencies)

    # --- 2. EMTİALAR ---
    commodities = [
        ("Brent Petrol", "BZ=F", ".2f"),
        ("Altın (Ons)", "GC=F", ".2f"),
        ("Gümüş", "SI=F", ".3f"),
        ("Doğalgaz", "NG=F", ".3f")
    ]
    display_metrics("🛢️ Stratejik Emtialar", commodities)

    # --- 3. KRİPTO VE ENDEKSLER ---
    crypto_indices = [
        ("Bitcoin (BTC)", "BTC-USD", ".0f"),
        ("S&P 500", "^GSPC", ".0f"),
        ("VIX (Korku)", "^VIX", ".2f"),
        ("DXY (Dolar Endeksi)", "DX-Y.NYB", ".2f")
    ]
    display_metrics("📊 Kripto & Endeksler", crypto_indices)
