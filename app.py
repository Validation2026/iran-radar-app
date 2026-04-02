import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import feedparser
from datetime import datetime, timedelta

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Jeopolitik Risk & Piyasa Radarı", page_icon="🌍")

# --- YAN MENÜ (SIDEBAR) ---
st.sidebar.title("⚙️ Kontrol Paneli")
st.sidebar.markdown("Zaman aralığını seçerek piyasaların tepkisini inceleyin.")
period = st.sidebar.selectbox("Finansal Veri Aralığı:", ["1 Ay", "3 Ay", "6 Ay", "1 Yıl"], index=0)

# Yfinance için periyot çevirici
period_dict = {"1 Ay": "1mo", "3 Ay": "3mo", "6 Ay": "6mo", "1 Yıl": "1y"}
selected_period = period_dict[period]

# --- ANA BAŞLIK ---
st.title("🌍 Jeopolitik Risk & Piyasa Radarı: İran")
st.markdown(
    "Bu interaktif panel, bölgedeki askeri/politik hareketlilikleri ve bunların küresel emtia ile korku endekslerine yansımasını anlık olarak takip eder.")
st.divider()

# --- SEKME (TAB) YAPISI ---
tab1, tab2, tab3 = st.tabs(["📍 Çatışma Haritası", "📈 Canlı Piyasa Etkisi", "📰 Son Dakika Canlı Akış"])

# --- TAB 1: HARİTA ---
with tab1:
    st.subheader("Bölgesel Sıcak Noktalar")
    st.markdown("Teyit edilmiş askeri hareketlilikler, vurulan hedefler veya stratejik risk taşıyan bölgeler.")

    # Gelişmiş Örnek Veriseti (Bunu ileride bir Google Sheets'e bağlayıp oradan da çekebilirsin)
    map_data = pd.DataFrame({
        "Bölge": ["Tahran (Başkent)", "İsfahan (Nükleer Tesis Yakını)", "Hürmüz Boğazı", "Tebriz", "Şiraz"],
        "Enlem": [35.6892, 32.6539, 26.5667, 38.0773, 29.5926],
        "Boylam": [51.3890, 51.6660, 56.2500, 46.2919, 52.5836],
        "Olay_Tipi": ["Siber Saldırı / Karargah", "Askeri Tesis İHA Saldırısı", "Petrol Sevkiyatı Tehdidi",
                      "Sınır Hareketliliği", "Hava Savunma Aktivitesi"],
        "Risk_Seviyesi": [4, 5, 5, 3, 3]  # 5 en yüksek risk
    })

    fig_map = px.scatter_mapbox(
        map_data, lat="Enlem", lon="Boylam", hover_name="Bölge", hover_data=["Olay_Tipi"],
        color="Risk_Seviyesi", size="Risk_Seviyesi",
        color_continuous_scale=px.colors.sequential.YlOrRd,  # Sarıdan kırmızıya risk haritası
        zoom=4, height=600, title="Risk ve Olay Haritası"
    )
    fig_map.update_layout(mapbox_style="carto-darkmatter")  # Gece modu harita (askeri radar hissi verir)
    st.plotly_chart(fig_map, use_container_width=True)

# --- TAB 2: FİNANSAL PİYASALAR ---
with tab2:
    st.subheader(f"Emtia ve Endeks Verileri (Son {period})")


    @st.cache_data(ttl=3600)  # Veriyi 1 saat önbellekte tutar, siteyi hızlandırır
    def get_finance_data(ticker, p):
        return yf.download(ticker, period=p)['Close']


    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.markdown("### 🛢️ Brent Petrol (Savaşın Yakıtı)")
        brent = get_finance_data("BZ=F", selected_period)
        st.line_chart(brent, color="#ffaa00")

    with col2:
        st.markdown("### 🥇 Altın (Güvenli Liman)")
        gold = get_finance_data("GC=F", selected_period)
        st.line_chart(gold, color="#ffd700")

    with col3:
        st.markdown("### 😨 VIX Endeksi (Küresel Korku)")
        st.caption("Piyasa paniğini ölçer. 30'un üzeri yüksek kriz demektir.")
        vix = get_finance_data("^VIX", selected_period)
        st.line_chart(vix, color="#ff0000")

    with col4:
        st.markdown("### 🥈 Gümüş (Endüstriyel & Değerli)")
        silver = get_finance_data("SI=F", selected_period)
        st.line_chart(silver, color="#c0c0c0")

# --- TAB 3: CANLI HABER AKIŞI ---
with tab3:
    st.subheader("📡 Otomatik Haber Akışı (Google News RSS)")
    st.markdown("Bölgeyle ilgili küresel basına düşen en son haberler otomatik olarak listelenir.")


    # RSS Çekme Fonksiyonu
    @st.cache_data(ttl=1800)  # Yarım saatte bir haberleri günceller
    def fetch_news():
        # Google News TR üzerinden İran ile ilgili haberleri çeker
        feed_url = "https://news.google.com/rss/search?q=İran+saldırı+OR+savaş+OR+çatışma&hl=tr&gl=TR&ceid=TR:tr"
        feed = feedparser.parse(feed_url)
        return feed.entries[:10]  # Son 10 haberi al


    news_items = fetch_news()

    if news_items:
        for item in news_items:
            with st.expander(f"🔴 {item.title}"):
                st.write(f"**Yayınlanma Tarihi:** {item.published}")
                st.markdown(f"[Haberin detayını oku ({item.source.title})]({item.link})")
    else:
        st.info("Şu an yeni haber çekilemedi.")

# --- FOOTER ---
st.divider()
st.caption("Bu veriler yfinance ve halka açık RSS servislerinden otomatik çekilmektedir. Yatırım tavsiyesi değildir.")