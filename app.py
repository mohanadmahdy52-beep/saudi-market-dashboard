import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import streamlit.components.v1 as components
import networkx as nx
import os

# 1. إعدادات الصفحة (يجب أن تكون أول سطر)
st.set_page_config(layout="wide", page_title="نبض السوق السعودي", page_icon="🇸🇦")

# ==========================================
# 🎨 التصميم السينمائي الفاخر (Dark Luxury)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Tajawal:wght@300;400;700;900&display=swap');

    /* 1. إزالة المساحات البيضاء العلوية تماماً */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        margin-top: 0rem !important;
    }
    header {visibility: hidden;}
    
    /* 2. الخلفية الداكنة الفخمة */
    .stApp {
        background: linear-gradient(135deg, #0b1013 0%, #1a2a33 50%, #102e3b 100%);
        font-family: 'Tajawal', sans-serif;
    }

    /* 3. العناوين والنصوص */
    h1, h2, h3, h4, .stMarkdown {
        font-family: 'Tajawal', sans-serif !important;
        color: #ffffff !important;
    }

    /* 4. الكروت الزجاجية (Glass Cards) */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        text-align: center;
        margin-bottom: 15px;
        transition: transform 0.3s;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
    }

    /* الأرقام الكبيرة */
    .big-number {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
    }
    .label-text {
        color: #aab6fe;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
    }

    /* تخصيص القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: #0b1013;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل وتنظيف البيانات (المنطق المصحح)
# ==========================================
@st.cache_data
def load_data():
    try:
        # قراءة الملف الرئيسي (15000 صف للأداء)
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', nrows=15000)
        
        # 1. إصلاح عمود المشاعر (الاعتماد على Sentiment)
        # توحيد الكلمات (إزالة المسافات وتوحيد الحروف)
        if 'Sentiment' in df.columns:
            df['Sentiment'] = df['Sentiment'].astype(str).str.strip().str.title() # يحولها Positive, Negative
            
            # خريطة للتأكد من القيم الشاذة
            sentiment_map = {
                'Positive': 'Positive', 'Pos': 'Positive', '1': 'Positive',
                'Negative': 'Negative', 'Neg': 'Negative', '-1': 'Negative',
                'Neutral': 'Neutral', 'Neu': 'Neutral', '0': 'Neutral'
            }
            df['Sentiment_Clean'] = df['Sentiment'].map(sentiment_map).fillna('Neutral')
        else:
            # لو العمود مش موجود، ننشئه افتراضياً (للطوارئ)
            df['Sentiment_Clean'] = 'Neutral'

        # 2. التأكد من عمود المدن
        if 'المدينة' not in df.columns:
            df['المدينة'] = 'غير محدد'

        # 3. التأكد من أعمدة الأسباب (للرسم البياني)
        if 'strategic_pillar' not in df.columns: df['strategic_pillar'] = 'غير مصنف'
        if 'macro_category' not in df.columns: df['macro_category'] = 'عام'

        # 4. دمج القطاعات من الملف الثاني (اختياري، لو موجود)
        try:
            df_cats = pd.read_excel("Saudi_CSR_Dataset.xlsx", engine='openpyxl', usecols=['نوع_النشاط', 'القطاع'])
            mapping = df_cats.drop_duplicates('نوع_النشاط').set_index('نوع_النشاط')['القطاع'].to_dict()
            df['Main_Sector'] = df['نوع_النشاط'].map(mapping).fillna(df['نوع_النشاط'])
        except:
            df['Main_Sector'] = df['نوع_النشاط'] # لو الملف التاني مش موجود استخدم النشاط نفسه

        # 5. معالجة التاريخ
        if 'Date_Clean' in df.columns:
            df['Date_Clean'] = pd.to_datetime(df['Date_Clean'], errors='coerce')

        return df
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        return pd.DataFrame()

# تنفيذ التحميل
df = load_data()

if df.empty:
    st.warning("⚠️ جاري تحميل البيانات...")
    st.stop()

# ==========================================
# 🔍 القائمة الجانبية (الفلاتر المصححة)
# ==========================================
st.sidebar.markdown("## ⚙️ إعدادات العرض")

# 1. فلتر المدينة (بدل المنطقة)
cities = ['الكل'] + sorted(list(df['المدينة'].astype(str).unique()))
sel_city = st.sidebar.selectbox("🏙️ المدينة", cities)

# 2. فلتر القطاع الرئيسي
sectors = ['الكل'] + sorted(list(df['Main_Sector'].astype(str).unique()))
sel_sector = st.sidebar.selectbox("🏢 القطاع", sectors)

# تطبيق الفلاتر
df_filtered = df.copy()
if sel_city != 'الكل':
    df_filtered = df_filtered[df_filtered['المدينة'] == sel_city]
if sel_sector != 'الكل':
    df_filtered = df_filtered[df_filtered['Main_Sector'] == sel_sector]

# ==========================================
# 🌟 القسم العلوي: العنوان + الباروميتر (Gauge)
# ==========================================

# حساب المؤشرات الحقيقية الآن
total = len(df_filtered)
pos = len(df_filtered[df_filtered['Sentiment_Clean'] == 'Positive'])
neg = len(df_filtered[df_filtered['Sentiment_Clean'] == 'Negative'])
# نسبة الرضا = (الإيجابي / الإجمالي) * 100
satisfaction_rate = int((pos / total) * 100) if total > 0 else 0

col_title, col_gauge = st.columns([1.5, 1])

with col_title:
    st.markdown("""
        <div style='padding-top: 20px;'>
            <h1 style='font-size: 3.2rem; background: -webkit-linear-gradient(#eee, #d4af37); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px;'>
                نبض السوق السعودي
            </h1>
            <p style='color: #aab6fe; font-size: 1.2rem;'>لوحة القيادة الاستراتيجية لقياس رضا المستفيدين في القطاع الخاص</p>
        </div>
    """, unsafe_allow_html=True)

with col_gauge:
    # رسم مؤشر السرعة (Gauge Chart)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = satisfaction_rate,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "مؤشر الرضا العام", 'font': {'size': 18, 'color': "white", 'family': "Tajawal"}},
        number = {'suffix': "%", 'font': {'color': "#d4af37", 'size': 40}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#d4af37"},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(231, 76, 60, 0.2)'}, # أحمر خفيف
                {'range': [50, 80], 'color': 'rgba(241, 196, 15, 0.2)'}, # أصفر خفيف
                {'range': [80, 100], 'color': 'rgba(80, 185, 101, 0.2)'}], # أخضر خفيف
        }))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=10, l=20, r=20), height=180)
    st.plotly_chart(fig_gauge, use_container_width=True)

# ==========================================
# 📊 بطاقات الأرقام (Cards)
# ==========================================
c1, c2, c3 = st.columns(3)

def card_html(label, value, color):
    return f"""
    <div class="glass-card">
        <div class="label-text">{label}</div>
        <div class="big-number" style="color: {color}">{value}</div>
    </div>
    """

with c1: st.markdown(card_html("إجمالي العينة المحللة", f"{total:,}", "#fff"), unsafe_allow_html=True)
with c2: st.markdown(card_html("تفاعل إيجابي (راضون)", f"{pos:,}", "#50b965"), unsafe_allow_html=True)
with c3: st.markdown(card_html("تفاعل سلبي (ساخطون)", f"{neg:,}", "#e74c3c"), unsafe_allow_html=True)

# ==========================================
# 📈 رسوم تحليل الأسباب (Root Cause Analysis)
# ==========================================
st.markdown("---")
st.markdown("### 🔍 لماذا يشتكي العملاء؟ (تحليل الأسباب الجذرية)")

row2_1, row2_2 = st.columns(2)

# رسم 1: الأسباب الاستراتيجية (Strategic Pillars)
with row2_1:
    if 'strategic_pillar' in df_filtered.columns:
        pillar_counts = df_filtered['strategic_pillar'].value_counts().head(5)
        fig_p = px.bar(pillar_counts, x=pillar_counts.values, y=pillar_counts.index, orientation='h',
                       title="أكبر المحاور الاستراتيجية للشكاوى",
                       color=pillar_counts.values, color_continuous_scale='Reds')
        fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family='Tajawal'))
        fig_p.update_coloraxes(showscale=False)
        st.plotly_chart(fig_p, use_container_width=True)

# رسم 2: التفاصيل الدقيقة (Macro Category)
with row2_2:
    if 'macro_category' in df_filtered.columns:
        # نأخذ الشكاوى السلبية فقط لأنها الأهم
        neg_issues = df_filtered[df_filtered['Sentiment_Clean'] == 'Negative']['macro_category'].value_counts().head(7)
        fig_m = px.pie(values=neg_issues.values, names=neg_issues.index, title="أكثر المشاكل الفرعية تكراراً",
                       color_discrete_sequence=px.colors.sequential.RdBu)
        fig_m.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family='Tajawal'))
        st.plotly_chart(fig_m, use_container_width=True)

# ==========================================
# 🕸️ التحليل الشبكي (The Network) - تم إصلاحه
# ==========================================
st.markdown("---")
st.markdown("### 🕸️ شبكة الترابط: (القطاع) vs (المشكلة)")
st.caption("توضح هذه الشبكة العلاقة بين القطاعات المختلفة وبين أنواع المشاكل التي تظهر فيها.")

# تجهيز البيانات للشبكة
# نأخذ عينة (مثلاً 100 صف) من البيانات السلبية لنرى الترابط
network_sample = df_filtered[df_filtered['Sentiment_Clean'] == 'Negative'].head(80)

if not network_sample.empty:
    G = nx.Graph()
    
    for i, row in network_sample.iterrows():
        sec = row['نوع_النشاط'] # المصدر
        prob = row['macro_category'] # الهدف
        
        # إضافة العقد
        G.add_node(sec, label=sec, title=sec, color='#13367', size=20, group='Sector')
        G.add_node(prob, label=prob, title=prob, color='#d4af37', size=15, group='Problem')
        # إضافة الرابط
        G.add_edge(sec, prob, color='rgba(255,255,255,0.2)')
    
    # إعدادات الفيزيائية للعرض
    nt = Network(height="500px", width="100%", bgcolor="#0b1013", font_color="white")
    nt.from_nx(G)
    nt.force_atlas_2based(gravity=-50) # توزيع الجاذبية لتباعد العقد
    
    # حفظ مؤقت وعرض
    try:
        path = 'network.html'
        nt.save_graph(path)
        with open(path, 'r', encoding='utf-8') as f:
            html_string = f.read()
        components.html(html_string, height=520)
    except:
        st.warning("⚠️ جاري تكوين الشبكة... يرجى الانتظار")
else:
    st.info("لا توجد بيانات سلبية كافية في هذا الفلتر لرسم الشبكة.")

# ==========================================
# 📊 الجدول التفصيلي للشفافية
# ==========================================
st.markdown("---")
with st.expander("عرض أحدث البيانات الخام (للشفافية)"):
    st.dataframe(df_filtered[['Date_Clean', 'المدينة', 'اسم_المنشأة', 'Sentiment_Clean', 'نص_المراجعة']].head(50))

st.markdown("<div style='text-align: center; color: #555; margin-top: 50px;'>Saudi Market Intelligence © 2026</div>", unsafe_allow_html=True)
