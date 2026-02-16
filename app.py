import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import streamlit.components.v1 as components
import networkx as nx

# 1. إعدادات الصفحة والهوية البصرية
st.set_page_config(layout="wide", page_title="Saudi Market Pulse", page_icon="🇸🇦")

# الألوان
PRIMARY_COLOR = "#13367"
SECONDARY_COLOR = "#50b965"
NEGATIVE_COLOR = "#FF4B4B"

# ستايل CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; }}
    h1, h2, h3 {{ color: {SECONDARY_COLOR} !important; font-family: 'Tajawal', sans-serif; }}
    .metric-card {{
        background-color: {PRIMARY_COLOR};
        border-left: 5px solid {SECONDARY_COLOR};
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. تحميل البيانات
@st.cache_data
def load_data():
    # ملاحظة: نقرأ 1000 صف فقط للتجربة السريعة
    # تأكد أن اسم الملف هنا يطابق اسم الملف المرفوع عندك 100%
    try:
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', nrows=1000)
    except FileNotFoundError:
        st.error("لم يتم العثور على الملف! تأكد من رفع 'Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx'")
        return pd.DataFrame()

    # معالجة البيانات
    if 'Date_Clean' in df.columns:
        df['Date_Clean'] = pd.to_datetime(df['Date_Clean'])
        df['Month_Year'] = df['Date_Clean'].dt.to_period('M').astype(str)
    
    if 'Sentiment' not in df.columns and 'Sentiment_Score' in df.columns:
        df['Sentiment'] = df['Sentiment_Score'].apply(lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral'))
    
    return df

# تشغيل التحميل
with st.spinner('جاري تشغيل المحرك الذكي...'):
    df = load_data()

if df.empty:
    st.stop()

# 3. القائمة الجانبية
st.sidebar.title("🔍 فلاتر التحكم")
selected_sector = st.sidebar.multiselect("القطاع", options=df['نوع_النشاط'].unique(), default=df['نوع_النشاط'].unique())
df_filtered = df[df['نوع_النشاط'].isin(selected_sector)]

# 4. الشاشة الرئيسية
st.title("📊 نبض السوق السعودي")
st.markdown("### رؤية تحليلية تفاعلية")

# المؤشرات
col1, col2, col3 = st.columns(3)
total = len(df_filtered)
pos = len(df_filtered[df_filtered['Sentiment'] == 'Positive'])
neg = len(df_filtered[df_filtered['Sentiment'] == 'Negative'])

with col1:
    st.markdown(f'<div class="metric-card"><h3>إجمالي العينة</h3><h1>{total}</h1></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>إيجابي</h3><h1 style="color:#4CAF50">{pos}</h1></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>سلبي</h3><h1 style="color:#FF4B4B">{neg}</h1></div>', unsafe_allow_html=True)

# الرسوم البيانية
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📈 توزيع المشاعر")
    fig_pie = px.pie(df_filtered, names='Sentiment', color_discrete_map={'Positive':'green', 'Negative':'red', 'Neutral':'gray'})
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.subheader("🏙️ التوزيع الجغرافي")
    if 'المدينة' in df_filtered.columns:
        city_counts = df_filtered['المدينة'].value_counts().head(5)
        fig_bar = px.bar(city_counts, x=city_counts.index, y=city_counts.values, color_discrete_sequence=[PRIMARY_COLOR])
        st.plotly_chart(fig_bar, use_container_width=True)

st.success("تم تشغيل النظام بنجاح! 🚀")

