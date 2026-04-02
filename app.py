import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import feedparser
import folium
from streamlit_folium import st_folium

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Detaylı OSINT & Piyasa Radarı", page_icon="🌍")

# --- YAN MENÜ ---
st.sidebar.title("⚙️ Kontrol Paneli")
st.sidebar.info("Açık Temayı tam hissetmek için: Sağ üstteki 3 noktaya (⋮) tıklayın -> Settings -> Theme -> 'Light' seçin.")
st.sidebar.markdown("---")
period = st.sidebar.selectbox("Finansal Veri Aralığını Seçin:", ["1 Ay", "3 Ay", "6 Ay", "1 Yıl"], index=0)
period_dict = {"1 Ay": "1mo", "3 Ay": "3mo", "6 Ay": "6mo", "1 Yıl": "1y"}
selected_period = period_dict[period]

# --- ANA BAŞLIK ---
st.title("🌍 Kapsamlı OSINT & Küresel Piyasalar Radarı")
st.markdown("Gerçek zamanlı operasyon haritası, doğrulanmış istihbarat, zayiat durumları ve küresel piyasaların geniş çaplı tepkisi.")
st.divider()

# --- SEKME YAPISI ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ OSINT Harekat Haritası", 
    "💱 Kapsamlı Küresel Piyasalar", 
    "💀 Liderlik & Stratejik Durum", 
    "📰 Doğrulanmış İstihbarat Akışı"
])

# --- TAB 1: FOLIUM OSINT HARİTASI (iranstrikemap benzeri) ---
with tab1:
    st.subheader("Doğrulanmış Operasyonlar & Bölgesel Etkiler")
    st.markdown("Hedeflerin üzerine tıklayarak OSINT kaynaklarına, zayiat bilgilerine ve detaylara ulaşabilirsiniz.")
    
    # Haritayı Açık Tema (CartoDB positron) ile başlatıyoruz (İran Merkezli)
    m = folium.Map(location=[32.4279, 53.6880], zoom_start=5, tiles="CartoDB positron")

    # Detaylı Olay Verisi (Veritabanı Simülasyonu)
    strike_data = [
        {"isim": "Tahran Askeri Tesis", "enlem": 35.6892, "boylam": 51.3890, "durum": "Doğrulandı - Ağır Hasar", "zayiat": "Bilinmiyor", "osint_link": "https://t.me/"},
        {"isim": "İsfahan Hava Üssü", "enlem": 32.6539, "boylam": 51.6660, "durum": "Doğrulandı - Pist Vuruldu", "zayiat": "3 Yaralı (Kızılay Raporu)", "osint_link": "https://twitter.com/"},
        {"isim": "Tebriz Füze Silosu", "enlem": 38.0773, "boylam": 46.2919, "durum": "Kısmi Hasar", "zayiat": "Yok", "osint_link": "https://t.me/"},
        {"isim": "Huzistan Petrol Rafinerisi", "enlem": 31.3273, "boylam": 48.6940, "durum": "Tehdit Altında - Üretim Durdu", "zayiat": "-", "osint_link": "https://news.google.com/"}
    ]

    # Haritaya Marker (İşaretçi) ve HTML Popup Ekleme
    for site in strike_data:
        html = f"""
        <div style="width:200px; font-family:sans-serif;">
            <h4 style="margin-bottom:5px; color:#b30000;">{site['isim']}</h4>
            <b>Durum:</b> {site['durum']}<br>
            <b>Zayiat:</b> {site['zayiat']}<br>
            <br>
            <a href="{site['osint_link']}" target="_blank" style="background-color:#004080; color:white; padding:5px; text-decoration:none; border-radius:3px;">🔗 OSINT / Video Kaynağı</a>
        </div>
        """
        iframe = folium.IFrame(html=html, width=220, height=140)
        popup = folium.Popup(iframe, max_width=220)
        
        folium.CircleMarker(
            location=[site['enlem'], site['boylam']],
            radius=9,
            popup=popup,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.7,
            tooltip=site['isim']
        ).add_to(m)

    # Haritayı Streamlit'e yansıtma
    st_folium(m, width=1200, height=600)


# --- TAB 2: KAPSAMLI FİNANSAL PİYASALAR ---
with tab2:
    st.subheader("Küresel Piyasalar ve Döviz Kurları Üzerindeki Etki")
    
    @st.cache_data(ttl=1800)
    def fetch_market_data(ticker, period):
        return yf.download(ticker, period=period)['Close']

    # Çizim fonksiyonu (Açık temaya uygun)
    def plot_sparkline(data, title, color):
        fig = go.Figure(go.Scatter(x=data.index, y=data.squeeze(), mode='lines', line=dict(color=color, width=2)))
        fig.update_layout(
            title=title, template="plotly_white", margin=dict(l=0, r=0, t=30, b=0),
            height=200, xaxis_visible=False, yaxis_visible=True
        )
        st.plotly_chart(fig, use_container_width=True)

    # Kategori 1: Dövizler
    st.markdown("#### 💵 Döviz Kurları")
    c1, c2, c3, c4 = st.columns(4)
    with c1: plot_sparkline(fetch_market_data("TRY=X", selected_period), "USD/TRY (Dolar)", "#0066cc")
    with c2: plot_sparkline(fetch_market_data("EURTRY=X", selected_period), "EUR/TRY (Euro)", "#004080")
    with c3: plot_sparkline(fetch_market_data("GBPTRY=X", selected_period), "GBP/TRY (Sterlin)", "#4b0082")
    with c4: plot_sparkline(fetch_market_data("CNYTRY=X", selected_period), "CNY/TRY (Yuan)", "#cc0000")

    # Kategori 2: Emtialar
    st.markdown("#### 🛢️ Stratejik Emtialar")
    c5, c6, c7 = st.columns(3)
    with c5: plot_sparkline(fetch_market_data("BZ=F", selected_period), "Brent Petrol", "#cc7a00")
    with c6: plot_sparkline(fetch_market_data("GC=F", selected_period), "Altın (Ons)", "#b38f00")
    with c7: plot_sparkline(fetch_market_data("NG=F", selected_period), "Doğalgaz", "#0080ff")

    c8, c9, c10 = st.columns(3)
    with c8: plot_sparkline(fetch_market_data("SI=F", selected_period), "Gümüş", "#808080")
    with c9: plot_sparkline(fetch_market_data("HG=F", selected_period), "Bakır (Endüstriyel)", "#b35900")
    with c10: plot_sparkline(fetch_market_data("ZW=F", selected_period), "Buğday (Gıda Kapsamı)", "#99cc00")

    # Kategori 3: Kripto & Endeksler
    st.markdown("#### 📊 Kripto ve Küresel Endeksler")
    c11, c12, c13 = st.columns(3)
    with c11: plot_sparkline(fetch_market_data("BTC-USD", selected_period), "Bitcoin", "#ff9900")
    with c12: plot_sparkline(fetch_market_data("^GSPC", selected_period), "S&P 500", "#009933")
    with c13: plot_sparkline(fetch_market_data("^VIX", selected_period), "VIX (Korku Endeksi)", "#e60000")


# --- TAB 3: LİDERLİK & STRATEJİK HEDEF DURUMU ---
with tab3:
    st.subheader("Üst Düzey Komuta ve Hedef Durumu")
    st.markdown("Tıpkı iranstrikemap'te olduğu gibi, hedef alınan veya teyit bekleyen liderlik statüleri.")
    
    col_hvt1, col_hvt2, col_hvt3 = st.columns(3)
    
    with col_hvt1:
        st.error("🔴 **Hedef A (Simülasyon)**")
        st.write("**Görevi:** Devrim Muhafızları Komutanı")
        st.write("**Son Konum:** Şam / Tahran")
        st.write("**Durum:** *Kritik - Haber Alınamıyor*")
    
    with col_hvt2:
        st.warning("🟠 **Hedef B (Simülasyon)**")
        st.write("**Görevi:** Nükleer Tesis Yöneticisi")
        st.write("**Son Konum:** İsfahan")
        st.write("**Durum:** *Teyit Edilmedi*")
        
    with col_hvt3:
        st.success("🟢 **Hedef C (Simülasyon)**")
        st.write("**Görevi:** Hava Savunma Sözcüsü")
        st.write("**Son Konum:** Tahran Karargahı")
        st.write("**Durum:** *Açıklama Yaptı - Aktif*")


# --- TAB 4: DOĞRULANMIŞ İSTİHBARAT HABERLERİ ---
with tab4:
    st.subheader("📰 Son Dakika Haber Akışı")
    
    @st.cache_data(ttl=1800)
    def fetch_news():
        feed_url = "https://news.google.com/rss/search?q=İran+saldırı+OR+savaş+OR+çatışma&hl=tr&gl=TR&ceid=TR:tr"
        feed = feedparser.parse(feed_url)
        return feed.entries[:15] # Haber sayısını artırdık

    news_items = fetch_news()
    
    if news_items:
        for item in news_items:
            st.markdown(f"**[{item.title}]({item.link})**")
            st.caption(f"🗓️ Yayınlanma: {item.published} | Kaynak: {item.source.title}")
            st.divider()
    else:
        st.info("Şu an yeni haber çekilemedi.")
