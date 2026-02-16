import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import streamlit.components.v1 as components
import networkx as nx

# 1. إعدادات الصفحة (يجب أن تكون أول سطر)
st.set_page_config(layout="wide", page_title="نبض السوق السعودي", page_icon="🇸🇦")

# ==========================================
# 🎨 التصميم الإبداعي المتحرك (CSS Magic)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;700;900&display=swap');

    /* 1. إلغاء المساحات البيضاء العلوية */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 2. الخلفية المتحركة (Aurora Effect) */
    .stApp {
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #13367);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        font-family: 'Tajawal', sans-serif;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 3. العناوين والنصوص */
    h1, h2, h3 {
        color: #fff !important;
        font-family: 'Tajawal', sans-serif !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }

    /* 4. الكروت الزجاجية (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        margin: 5px;
        text-align: center;
        transition: transform 0.3s;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border: 1px solid #d4af37;
        background: rgba(255, 255, 255, 0.1);
    }

    /* 5. تخصيص الفلاتر */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* أرقام المؤشرات */
    .big-number {
        font-size: 2.5rem;
        font-weight: 900;
        background: -webkit-linear-gradient(#fff, #d4af37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل ومعالجة البيانات (Fixing Zeros)
# ==========================================
@st.cache_data
def load_data():
    try:
        # قراءة 15,000 صف
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', nrows=15000)
        
        # 🛠️ إصلاح البيانات (Critical Fixes)
        
        # 1. تحويل التاريخ
        if 'Date_Clean' in df.columns:
            df['Date_Clean'] = pd.to_datetime(df['Date_Clean'], errors='coerce')
        
        # 2. التأكد من أن عمود التقييم رقمي (لحل مشكلة الأصفار)
        # نبحث عن العمود ونحوله لرقم غصباً عنه
        score_col = None
        possible_names = ['Sentiment_Score', 'Score', 'sentiment_score', 'التقييم', 'Sentiment']
        for col in possible_names:
            if col in df.columns:
                # محاولة تحويل العمود لأرقام، وأي نص يتحول لـ NaN
                if pd.api.types.is_numeric_dtype(df[col]):
                     score_col = col
                     break
                else:
                    # محاولة التحويل القسري
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].notna().sum() > 0: # لو فيه أرقام ظهرت
                        score_col = col
                        break
        
        if score_col:
            df['Final_Score'] = df[score_col]
            # تصنيف المشاعر من جديد بناءً على الأرقام
            df['Sentiment_Label'] = df['Final_Score'].apply(
                lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral')
            )
        else:
            # بيانات وهمية لو فشل كل شيء عشان الموقع لا يقع
            df['Final_Score'] = 0
            df['Sentiment_Label'] = 'Neutral'

        # 3. رسم خريطة المناطق (Mapping)
        # بما أن المناطق قد لا تكون موجودة، سنصنعها من المدن
        regions_map = {
            'Riyadh': 'الوسطى', 'الرياض': 'الوسطى',
            'Jeddah': 'الغربية', 'جدة': 'الغربية', 'Mecca': 'الغربية', 'مكة': 'الغربية', 'Medina': 'الغربية', 'المدينة': 'الغربية',
            'Dammam': 'الشرقية', 'الدمام': 'الشرقية', 'Khobar': 'الشرقية', 'الخبر': 'الشرقية',
            'Abha': 'الجنوبية', 'أبها': 'الجنوبية', 'Jazan': 'الجنوبية', 'جازان': 'الجنوبية',
            'Tabuk': 'الشمالية', 'تبوك': 'الشمالية', 'Hail': 'الشمالية', 'حائل': 'الشمالية'
        }
        if 'المدينة' in df.columns:
            df['Region'] = df['المدينة'].map(regions_map).fillna('أخرى')
        else:
            df['Region'] = 'غير محدد'

        # 4. التأكد من وجود عمود للمشاكل
        if 'macro_category' not in df.columns:
            df['macro_category'] = 'عام'

        return df
    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ جاري تحميل البيانات... يرجى الانتظار")
    st.stop()

# ==========================================
# 🔍 القائمة الجانبية (فلاتر متقدمة)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/323/323310.png", width=80)
st.sidebar.markdown("### ⚙️ إعدادات التحليل")

# 1. فلتر المنطقة
regions = ['الكل'] + sorted(list(df['Region'].unique()))
sel_region = st.sidebar.selectbox("🗺️ المنطقة", regions)

# 2. فلتر القطاع الرئيسي
sectors = ['الكل'] + sorted(list(df['نوع_النشاط'].unique()))
sel_sector = st.sidebar.selectbox("🏢 القطاع", sectors)

# 3. فلتر نوع المشكلة
problems = ['الكل'] + sorted(list(df['macro_category'].astype(str).unique()))
sel_problem = st.sidebar.selectbox("⚠️ نوع المشكلة", problems)

# تطبيق الفلاتر
df_filtered = df.copy()
if sel_region != 'الكل':
    df_filtered = df_filtered[df_filtered['Region'] == sel_region]
if sel_sector != 'الكل':
    df_filtered = df_filtered[df_filtered['نوع_النشاط'] == sel_sector]
if sel_problem != 'الكل':
    df_filtered = df_filtered[df_filtered['macro_category'] == sel_problem]

# ==========================================
# 🌟 القسم العلوي: المؤشر العام (Hero Section)
# ==========================================

# حساب المؤشرات
total_rev = len(df_filtered)
pos_rev = len(df_filtered[df_filtered['Sentiment_Label'] == 'Positive'])
neg_rev = len(df_filtered[df_filtered['Sentiment_Label'] == 'Negative'])
# حساب نسبة الرضا (تجنب القسمة على صفر)
satisfaction_rate = int((pos_rev / total_rev) * 100) if total_rev > 0 else 0

# عنوان ومؤشر ضخم
col_hero1, col_hero2 = st.columns([2, 1])

with col_hero1:
    st.markdown(f"""
    <div>
        <h1 style='font-size: 3rem; margin-bottom: 0;'>نبض السوق السعودي</h1>
        <p style='color: #ddd; font-size: 1.2rem; margin-top: 0;'>منصة استشراف المستقبل وتحليل رضا المستفيدين</p>
    </div>
    """, unsafe_allow_html=True)

with col_hero2:
    # مؤشر دائري ضخم
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = satisfaction_rate,
        title = {'text': "مؤشر الرضا العام", 'font': {'size': 20, 'color': 'white', 'family': 'Tajawal'}},
        number = {'suffix': "%", 'font': {'color': '#d4af37'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#d4af37"},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [50, 100], 'color': 'rgba(0, 255, 0, 0.3)'}],
        }))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=0, b=0, l=20, r=20), height=150)
    st.plotly_chart(fig_gauge, use_container_width=True)

# ==========================================
# 📊 شريط القطاعات (Sector Squares)
# ==========================================
st.markdown("### 🏢 مؤشرات القطاعات الرئيسية")

# نأخذ أكبر 5 قطاعات كعينة
top_sectors = df['نوع_النشاط'].value_counts().head(5).index
cols = st.columns(len(top_sectors))

for i, sec in enumerate(top_sectors):
    sec_data = df[df['نوع_النشاط'] == sec]
    sec_sat = len(sec_data[sec_data['Sentiment_Label'] == 'Positive']) / len(sec_data) * 100 if len(sec_data) > 0 else 0
    color = "#50b965" if sec_sat >= 70 else ("#f1c40f" if sec_sat >= 50 else "#e74c3c")
    
    with cols[i]:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:0.9rem; color:#ccc;">{sec}</div>
            <div class="big-number" style="font-size: 1.8rem; -webkit-text-fill-color: {color};">{int(sec_sat)}%</div>
            <div style="font-size:0.8rem; color:#fff;">نسبة الرضا</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 📈 الرسوم البيانية (Charts)
# ==========================================
st.markdown("---")
row1_col1, row1_col2 = st.columns([2, 1])

# 1. رسم المناطق (Bar Chart)
with row1_col1:
    st.markdown("### 🌍 مستويات الرضا حسب المنطقة")
    region_stats = df_filtered.groupby('Region')['Final_Score'].mean().reset_index()
    # تحويل السكور لنسبة مئوية تقريبية للرسم
    region_stats['Percentage'] = ((region_stats['Final_Score'] + 1) / 2 * 100).fillna(0) # تقريبي من -1:1 إلى 0:100
    
    fig_region = px.bar(region_stats, x='Region', y='Percentage', color='Percentage', 
                        color_continuous_scale='RdYlGn', text_auto='.1f')
    fig_region.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                             font=dict(color='white', family='Tajawal'), margin=dict(t=20, l=0, r=0, b=0))
    st.plotly_chart(fig_region, use_container_width=True)

# 2. تحليل المشاعر (Donut)
with row1_col2:
    st.markdown("### 🎭 توزيع المشاعر")
    fig_donut = px.donut(df_filtered, names='Sentiment_Label', 
                         color='Sentiment_Label',
                         color_discrete_map={'Positive':'#50b965', 'Negative':'#e74c3c', 'Neutral':'#95a5a6'},
                         hole=0.6)
    fig_donut.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white', family='Tajawal'), showlegend=False,
                            margin=dict(t=20, l=0, r=0, b=0))
    
    # وضع النسبة في النص
    fig_donut.add_annotation(text=f"{satisfaction_rate}%", showarrow=False, 
                             font=dict(size=30, color="white", family="Tajawal"))
    st.plotly_chart(fig_donut, use_container_width=True)

# 3. المسار الزمني (Area Chart)
st.markdown("### 📈 المسار الزمني للرضا (Time Trend)")
if 'Date_Clean' in df_filtered.columns:
    trend = df_filtered.groupby(df_filtered['Date_Clean'].dt.to_period('M'))['Final_Score'].mean().reset_index()
    trend['Date_Clean'] = trend['Date_Clean'].astype(str)
    
    fig_trend = px.area(trend, x='Date_Clean', y='Final_Score', markers=True)
    fig_trend.update_traces(line_color='#d4af37', fillcolor='rgba(212, 175, 55, 0.2)')
    fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white', family='Tajawal'), 
                            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'))
    st.plotly_chart(fig_trend, use_container_width=True)

# ==========================================
# 🕸️ التحليل الشبكي (Network Graph)
# ==========================================
st.markdown("---")
st.markdown("### 🕸️ شبكة العلاقات: ما الذي يربط المشاكل بالقطاعات؟")
st.caption("💡 هذه الشبكة تفاعلية! يمكنك تحريك العناصر وتقريب الصورة.")

# تجهيز البيانات للشبكة (نأخذ عينة من الشكاوى فقط لعدم تعليق المتصفح)
net_data = df_filtered[df_filtered['Sentiment_Label'] == 'Negative'].head(100) # أول 100 مشكلة سلبية

if not net_data.empty:
    G = nx.Graph()
    
    for i, row in net_data.iterrows():
        # العقدة 1: القطاع
        sector_node = row['نوع_النشاط']
        # العقدة 2: المشكلة
        problem_node = row['macro_category']
        
        G.add_node(sector_node, label=sector_node, color='#50b965', size=20, title="قطاع")
        G.add_node(problem_node, label=problem_node, color='#e74c3c', size=15, title="مشكلة")
        G.add_edge(sector_node, problem_node, color='rgba(255,255,255,0.3)')

    # رسم الشبكة
    nt = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    nt.from_nx(G)
    nt.hrepulsion() # تباعد الفيزيائي للعقد
    
    # حفظ وعرض
    try:
        path = '/tmp'
        nt.save_graph(f'network.html')
        HtmlFile = open(f'network.html', 'r', encoding='utf-8')
        source_code = HtmlFile.read() 
        components.html(source_code, height=510)
    except:
        st.warning("⚠️ الشبكة تحتاج بيئة محلية للكتابة، لكن البيانات جاهزة.")
else:
    st.info("لا توجد بيانات سلبية كافية لرسم شبكة المشاكل في هذا الفلتر.")

# تذييل الصفحة
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Developed with ❤️ for Saudi Vision 2030</div>", unsafe_allow_html=True)
