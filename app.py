import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Saudi Market Pulse", page_icon="💎")

# ==========================================
# 🎨 التصميم السينمائي الفاخر (Fixed)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Tajawal:wght@300;400;700&display=swap');

    /* خلفية متدرجة (Night Mode Luxury) */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Tajawal', sans-serif;
    }

    /* العناوين المذهبة */
    h1, h2, h3, h4 {
        font-family: 'Tajawal', sans-serif !important;
        color: #e0c3fc !important;
        text-shadow: 0px 0px 10px rgba(224, 195, 252, 0.2);
    }
    
    /* الكروت الزجاجية */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(7px);
        -webkit-backdrop-filter: blur(7px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        padding: 20px;
        text-align: center;
        transition: transform 0.2s;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
    }
    
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: bold;
        color: #fff;
    }
    .metric-label {
        color: #aab6fe;
        font-size: 0.9rem;
        letter-spacing: 1px;
    }
    
    /* تخصيص القوائم */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.98);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل البيانات (النسخة المرنة)
# ==========================================
@st.cache_data
def load_data():
    try:
        # التعديل: أزلنا usecols لتجنب خطأ الأسماء، وقرأنا 15000 صف
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', nrows=15000)
        
        # تنظيف وتجهيز البيانات
        if 'Date_Clean' in df.columns:
            df['Date_Clean'] = pd.to_datetime(df['Date_Clean'])
        
        # معالجة عمود المشاعر (التعامل مع احتمالات مختلفة للاسم)
        # نحاول العثور على عمود التقييم سواء كان اسمه Score أو Sentiment
        score_col = None
        for col in ['Sentiment_Score', 'Score', 'sentiment_score', 'score']:
            if col in df.columns:
                score_col = col
                break
        
        if score_col:
            df['Sentiment'] = df[score_col].apply(lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral'))
            df['Final_Score'] = df[score_col] # توحيد الاسم
        else:
            # لو مفيش سكور، نعتبره محايد (احتياطي)
            df['Sentiment'] = 'Neutral'
            df['Final_Score'] = 0

        return df
    except Exception as e:
        st.error(f"حدث خطأ في قراءة الملف: {e}")
        return None

# تنفيذ التحميل
with st.spinner('جاري تشغيل محرك الذكاء الاصطناعي...'):
    df = load_data()

if df is None:
    st.stop()

# ==========================================
# 🏠 الواجهة الرئيسية (Hero Section)
# ==========================================

st.markdown("""
    <div style='text-align: center; margin-bottom: 40px;'>
        <h1 style='font-size: 3.5rem; background: -webkit-linear-gradient(#eee, #d4af37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            نبض السوق السعودي
        </h1>
        <p style='color: #888; font-size: 1.2rem;'>AI-Powered Strategic Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# الفلاتر
st.sidebar.markdown("### ⚙️ إعدادات التحليل")
if 'نوع_النشاط' in df.columns:
    sectors = sorted(df['نوع_النشاط'].unique().astype(str))
    selected_sector = st.sidebar.multiselect("القطاع", sectors, default=sectors[:1])
    if selected_sector:
        df_filtered = df[df['نوع_النشاط'].isin(selected_sector)]
    else:
        df_filtered = df
else:
    df_filtered = df

# حسابات المؤشرات
total_rev = len(df_filtered)
pos_rev = len(df_filtered[df_filtered['Sentiment'] == 'Positive'])
neg_rev = len(df_filtered[df_filtered['Sentiment'] == 'Negative'])
satisfaction = int((pos_rev / total_rev * 100)) if total_rev > 0 else 0

# عرض الكروت
c1, c2, c3, c4 = st.columns(4)
def card_html(label, value, color="#fff"):
    return f"""
    <div class="glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {color}">{value}</div>
    </div>
    """

with c1: st.markdown(card_html("حجم البيانات", f"{total_rev:,}"), unsafe_allow_html=True)
with c2: st.markdown(card_html("مؤشر الرضا", f"{satisfaction}%", "#d4af37"), unsafe_allow_html=True)
with c3: st.markdown(card_html("إيجابي", f"{pos_rev:,}", "#50b965"), unsafe_allow_html=True)
with c4: st.markdown(card_html("سلبي", f"{neg_rev:,}", "#ff6b6b"), unsafe_allow_html=True)

# ==========================================
# 📊 الرسوم البيانية (Charts)
# ==========================================
st.markdown("---")
chart_config = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="Tajawal"))

col_main1, col_main2 = st.columns([2, 1])

with col_main1:
    st.markdown("### 📈 المسار الزمني")
    if 'Date_Clean' in df_filtered.columns:
        trend = df_filtered.groupby(df_filtered['Date_Clean'].dt.to_period('M'))['Final_Score'].mean().reset_index()
        trend['Date_Clean'] = trend['Date_Clean'].astype(str)
        fig_trend = px.area(trend, x='Date_Clean', y='Final_Score', color_discrete_sequence=['#d4af37'])
        fig_trend.update_layout(**chart_config)
        st.plotly_chart(fig_trend, use_container_width=True)

with col_main2:
    st.markdown("### 🎭 تحليل المشاعر")
    fig_donut = px.donut(df_filtered, names='Sentiment', color='Sentiment', 
                         color_discrete_map={'Positive':'#50b965', 'Negative':'#ff6b6b', 'Neutral':'#888'}, hole=0.6)
    fig_donut.update_layout(**chart_config, showlegend=False)
    fig_donut.add_annotation(text=f"{satisfaction}%", showarrow=False, font=dict(size=25, color="white"))
    st.plotly_chart(fig_donut, use_container_width=True)

# خريطة المدن
st.markdown("### 🌍 الخارطة الحرارية للمدن")
if 'المدينة' in df_filtered.columns:
    city_counts = df_filtered['المدينة'].value_counts().head(7)
    fig_city = px.bar(city_counts, x=city_counts.values, y=city_counts.index, orientation='h', 
                      color=city_counts.values, color_continuous_scale='Tealgrn')
    fig_city.update_layout(**chart_config)
    fig_city.update_coloraxes(showscale=False)
    st.plotly_chart(fig_city, use_container_width=True)

# ==========================================
# 💬 الشريط الإخباري (Live Feed)
# ==========================================
st.markdown("### 📢 أحدث آراء المجتمع")
# نحاول نجيب نص المراجعة، لو مش موجود نجيب أي عمود نصي
text_col = 'نص_المراجعة' if 'نص_المراجعة' in df.columns else None
name_col = 'اسم_المنشأة' if 'اسم_المنشأة' in df.columns else None

if text_col and name_col:
    for i, row in df_filtered.head(3).iterrows():
        color_bar = "#50b965" if row['Sentiment'] == 'Positive' else "#ff6b6b"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border-radius: 10px; padding: 15px; border-right: 4px solid {color_bar}; margin-bottom: 10px;">
            <div style="color: #d4af37; font-weight: bold; font-size: 1.1rem;">{row[name_col]}</div>
            <div style="color: #ddd; margin-top: 5px;">"{row[text_col]}"</div>
        </div>
        """, unsafe_allow_html=True)
