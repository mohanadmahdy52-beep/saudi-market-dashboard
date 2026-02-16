import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة (يجب أن تكون في أول سطر)
st.set_page_config(layout="wide", page_title="Saudi Market Pulse", page_icon="💎")

# ==========================================
# 🎨 قسم التصميم السينمائي (Dark Luxury Theme)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Tajawal:wght@300;400;700&display=swap');

    /* خلفية متدرجة فخمة */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Tajawal', sans-serif;
    }

    /* العناوين الذهبية */
    h1, h2, h3 {
        font-family: 'Tajawal', sans-serif !important;
        color: #e0c3fc !important;
        text-shadow: 0px 0px 10px rgba(224, 195, 252, 0.3);
    }
    
    /* البطاقات الزجاجية */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border: 1px solid #d4af37;
    }
    
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        font-weight: bold;
        color: #fff;
    }
    .metric-label {
        color: #aab6fe;
        font-size: 1rem;
        margin-bottom: 5px;
    }
    
    /* تخصيص القوائم */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل البيانات (النسخة الآمنة)
# ==========================================
@st.cache_data
def load_data():
    try:
        # قراءة 15,000 صف فقط للحفاظ على سرعة واستقرار الموقع المجاني
        # هذا العدد كافي جداً لإظهار التوزيعات والنسب بدقة
        cols = ['نوع_النشاط', 'المدينة', 'Sentiment_Score', 'Date_Clean', 'نص_المراجعة', 'اسم_المنشأة']
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', usecols=cols, nrows=15000)
        
        # معالجة البيانات
        df['Date_Clean'] = pd.to_datetime(df['Date_Clean'])
        df['Sentiment'] = df['Sentiment_Score'].apply(lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral'))
        return df
    except Exception as e:
        st.error(f"خطأ تقني: {e}")
        return None

# مؤشر التحميل
with st.spinner('جاري بناء واجهة الذكاء الاصطناعي...'):
    df = load_data()

if df is None:
    st.warning("⚠️ يرجى التأكد من اسم ملف الإكسل في GitHub.")
    st.stop()

# ==========================================
# 🏠 الواجهة الرئيسية
# ==========================================

# العنوان
st.markdown("""
    <div style='text-align: center; padding: 40px 0;'>
        <h1 style='font-size: 3rem; background: -webkit-linear-gradient(#eee, #d4af37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            نبض السوق السعودي
        </h1>
        <p style='color: #ccc; font-size: 1.1rem;'>لوحة قيادة تفاعلية مدعومة بالبيانات الضخمة</p>
    </div>
""", unsafe_allow_html=True)

# القائمة الجانبية
st.sidebar.markdown("### ⚙️ إعدادات العرض")
sectors = sorted(df['نوع_النشاط'].unique())
selected_sector = st.sidebar.multiselect("تصفية حسب القطاع", sectors, default=sectors[:1])

if selected_sector:
    df_filtered = df[df['نوع_النشاط'].isin(selected_sector)]
else:
    df_filtered = df

# المؤشرات (KPIs)
total = len(df_filtered)
pos = len(df_filtered[df_filtered['Sentiment'] == 'Positive'])
neg = len(df_filtered[df_filtered['Sentiment'] == 'Negative'])
sat_rate = int((pos/total)*100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)

def kpi_card(label, value, color="#fff"):
    return f"""
    <div class="glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {color}">{value}</div>
    </div>
    """

with col1: st.markdown(kpi_card("حجم العينة", f"{total:,}"), unsafe_allow_html=True)
with col2: st.markdown(kpi_card("معدل الرضا", f"{sat_rate}%", "#d4af37"), unsafe_allow_html=True)
with col3: st.markdown(kpi_card("تفاعل إيجابي", f"{pos:,}", "#50b965"), unsafe_allow_html=True)
with col4: st.markdown(kpi_card("تفاعل سلبي", f"{neg:,}", "#ff6b6b"), unsafe_allow_html=True)

# ==========================================
# 📊 الرسوم البيانية
# ==========================================
st.markdown("---")
layout_style = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="Tajawal"))

c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("### 📈 المسار الزمني")
    trend = df_filtered.groupby(df_filtered['Date_Clean'].dt.to_period('M'))['Sentiment_Score'].mean().reset_index()
    trend['Date_Clean'] = trend['Date_Clean'].astype(str)
    fig_trend = px.area(trend, x='Date_Clean', y='Sentiment_Score', color_discrete_sequence=['#d4af37'])
    fig_trend.update_layout(**layout_style)
    st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.markdown("### 🎭 تحليل المشاعر")
    fig_pie = px.donut(df_filtered, names='Sentiment', color='Sentiment', 
                       color_discrete_map={'Positive':'#50b965', 'Negative':'#ff6b6b', 'Neutral':'#888'}, hole=0.6)
    fig_pie.update_layout(**layout_style, showlegend=False)
    fig_pie.add_annotation(text=f"{sat_rate}%", showarrow=False, font=dict(size=20, color="white"))
    st.plotly_chart(fig_pie, use_container_width=True)

# المدن
st.markdown("### 🌍 خريطة المدن")
city_data = df_filtered['المدينة'].value_counts().head(7)
fig_bar = px.bar(city_data, x=city_data.values, y=city_data.index, orientation='h', color=city_data.values, color_continuous_scale='Tealgrn')
fig_bar.update_layout(**layout_style)
fig_bar.update_coloraxes(showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)


