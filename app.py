import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. إعدادات الصفحة (يجب أن تكون في أول سطر)
st.set_page_config(layout="wide", page_title="Saudi Market Pulse", page_icon="💎")

# ==========================================
# 🎨 قسم التصميم السحري (CSS Injection)
# ==========================================
# هنا نغير جلد الموقع بالكامل ليصبح مثل العروض العالمية
st.markdown("""
    <style>
    /* استيراد خطوط راقية: تجوال للعربي، وبلاي فير للعناوين الإنجليزية */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Tajawal:wght@300;400;700&display=swap');

    /* خلفية متدرجة فخمة (Dark Luxury Gradient) */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Tajawal', sans-serif;
    }

    /* العناوين (تأثير ذهبي) */
    h1, h2, h3 {
        font-family: 'Tajawal', sans-serif !important;
        color: #e0c3fc !important;
        text-shadow: 0px 0px 10px rgba(224, 195, 252, 0.3);
    }
    
    h1 {
        background: -webkit-linear-gradient(#eee, #d4af37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        font-weight: 900 !important;
    }

    /* البطاقات الزجاجية (Glassmorphism Cards) */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        border: 1px solid #d4af37; /* حدود ذهبية عند اللمس */
    }

    /* الأرقام داخل البطاقات */
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffffff;
    }
    
    .metric-label {
        color: #aab6fe;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }

    /* تخصيص القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل البيانات (كاملة مع كاش)
# ==========================================
@st.cache_data
def load_data():
    # تمت إزالة nrows=1000 لقراءة الملف كاملاً
    try:
        # قراءة الأعمدة المهمة فقط لتسريع الأداء
        cols = ['نوع_النشاط', 'المدينة', 'Sentiment_Score', 'Date_Clean', 'نص_المراجعة', 'اسم_المنشأة']
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', usecols=cols)
        
        # معالجة سريعة
        df['Date_Clean'] = pd.to_datetime(df['Date_Clean'])
        df['Sentiment'] = df['Sentiment_Score'].apply(lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral'))
        return df
    except Exception as e:
        return None

# مؤشر تحميل أنيق
with st.spinner('جاري استدعاء مؤشرات السوق السعودي...'):
    df = load_data()

if df is None:
    st.error("⚠️ يرجى التأكد من رفع ملف البيانات: Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx")
    st.stop()

# ==========================================
# 🎛️ القائمة الجانبية (Control Panel)
# ==========================================
st.sidebar.markdown("<h2 style='color:#d4af37 !important;'>⚙️ فلاتر التحكم</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

sectors = sorted(df['نوع_النشاط'].unique())
selected_sector = st.sidebar.multiselect("اختر القطاع", sectors, default=sectors[:1])

cities = sorted(df['المدينة'].unique())
selected_city = st.sidebar.multiselect("اختر المدينة", cities)

# تطبيق الفلتر
df_filtered = df.copy()
if selected_sector:
    df_filtered = df_filtered[df_filtered['نوع_النشاط'].isin(selected_sector)]
if selected_city:
    df_filtered = df_filtered[df_filtered['المدينة'].isin(selected_city)]

# ==========================================
# 🏠 الواجهة الرئيسية (The Hero Section)
# ==========================================

# العنوان الرئيسي بتصميم مبهج
st.markdown("""
    <div style='text-align: center; padding: 50px 0;'>
        <h1>نبض السوق السعودي</h1>
        <p style='color: #ccc; font-size: 1.2rem;'>منصة ذكاء الأعمال لتحليل انطباعات المستهلكين باستخدام AI</p>
    </div>
""", unsafe_allow_html=True)

# حساب المؤشرات
total_reviews = len(df_filtered)
pos_count = len(df_filtered[df_filtered['Sentiment'] == 'Positive'])
neg_count = len(df_filtered[df_filtered['Sentiment'] == 'Negative'])
satisfaction_pct = int((pos_count / total_reviews * 100)) if total_reviews > 0 else 0

# عرض البطاقات (Cards) باستخدام HTML مخصص
col1, col2, col3, col4 = st.columns(4)

def card(title, value, color="#fff"):
    return f"""
    <div class="glass-card">
        <div class="metric-label">{title}</div>
        <div class="metric-value" style="color: {color}">{value}</div>
    </div>
    """

with col1:
    st.markdown(card("إجمالي العينة", f"{total_reviews:,}"), unsafe_allow_html=True)
with col2:
    st.markdown(card("مؤشر الرضا العام", f"{satisfaction_pct}%", "#d4af37"), unsafe_allow_html=True) # ذهبي
with col3:
    st.markdown(card("تفاعل إيجابي", f"{pos_count:,}", "#50b965"), unsafe_allow_html=True) # أخضر
with col4:
    st.markdown(card("تفاعل سلبي", f"{neg_count:,}", "#ff6b6b"), unsafe_allow_html=True) # أحمر

# ==========================================
# 📊 الرسوم البيانية (Plotly Dark Theme)
# ==========================================
st.markdown("---")

col_g1, col_g2 = st.columns([2, 1])

# إعداد ثيم الرسوم ليكون شفافاً
layout_settings = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white', family="Tajawal"),
    margin=dict(t=50, l=20, r=20, b=20)
)

with col_g1:
    st.markdown("### 📈 المسار الزمني للرضا")
    daily_trend = df_filtered.groupby(df_filtered['Date_Clean'].dt.to_period('M'))['Sentiment_Score'].mean().reset_index()
    daily_trend['Date_Clean'] = daily_trend['Date_Clean'].astype(str)
    
    fig_trend = px.area(daily_trend, x='Date_Clean', y='Sentiment_Score', 
                        color_discrete_sequence=['#d4af37']) # لون ذهبي
    fig_trend.update_layout(**layout_settings)
    fig_trend.update_xaxes(showgrid=False)
    fig_trend.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    st.plotly_chart(fig_trend, use_container_width=True)

with col_g2:
    st.markdown("### 🎭 تحليل المشاعر")
    fig_pie = px.donut(df_filtered, names='Sentiment', 
                       color='Sentiment',
                       color_discrete_map={'Positive':'#50b965', 'Negative':'#ff6b6b', 'Neutral':'#888'},
                       hole=0.6)
    fig_pie.update_layout(**layout_settings, showlegend=False)
    # إضافة نص في وسط الدائرة
    fig_pie.add_annotation(text=f"{satisfaction_pct}%", x=0.5, y=0.5, font_size=25, showarrow=False, font_color="white")
    st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# 🏙️ تحليل المدن والمنشآت
# ==========================================
st.markdown("### 🌍 الخارطة الحرارية للمدن")
city_stats = df_filtered.groupby('المدينة')['Sentiment_Score'].mean().sort_values().head(10)
fig_bar = px.bar(city_stats, x=city_stats.values, y=city_stats.index, orientation='h',
                 color=city_stats.values, color_continuous_scale='RdYlGn')

fig_bar.update_layout(**layout_settings)
fig_bar.update_coloraxes(showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 💬 أحدث الأصوات (Live Feed)
# ==========================================
st.markdown("### 📢 أحدث أصوات المستهلكين")
for i, row in df_filtered.head(3).iterrows():
    sentiment_color = "#50b965" if row['Sentiment'] == 'Positive' else "#ff6b6b"
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border-right: 5px solid {sentiment_color}; margin-bottom: 10px;">
        <small style="color: #888;">{row['Date_Clean'].strftime('%Y-%m-%d')} | {row['المدينة']}</small><br>
        <strong style="color: #fff; font-size: 1.1rem;">{row['اسم_المنشأة']}</strong>
        <p style="color: #ddd; margin-top: 5px;">"{row['نص_المراجعة']}"</p>
    </div>
    """, unsafe_allow_html=True)

