import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import streamlit.components.v1 as components
import networkx as nx

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="نبض السوق السعودي", page_icon="💎")

# ==========================================
# 🎨 التصميم السينمائي الموحد (Unified Luxury Theme)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Tajawal:wght@300;400;700;900&display=swap');

    /* إلغاء الهوامش */
    .block-container { padding-top: 0rem !important; padding-bottom: 2rem !important; }
    header {visibility: hidden;}
    
    /* الخلفية الداكنة الموحدة */
    .stApp {
        background: linear-gradient(135deg, #0b1013 0%, #1a2a33 50%, #102e3b 100%);
        font-family: 'Tajawal', sans-serif;
        color: white;
    }

    /* العناوين الذهبية */
    h1, h2, h3 {
        font-family: 'Tajawal', sans-serif !important;
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    }

    /* الكروت الزجاجية (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        text-align: center;
        transition: transform 0.3s;
        height: 100%;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
        background: rgba(255, 255, 255, 0.08);
    }

    /* الأرقام */
    .big-number {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #fff;
    }

    /* القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: #080c0e;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* إزالة حدود الفريمات لجعل الشبكة متداخلة */
    iframe { border: none !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل البيانات
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', nrows=15000)
        
        # تنظيف المشاعر
        if 'Sentiment' in df.columns:
            df['Sentiment'] = df['Sentiment'].astype(str).str.strip().str.title()
            sentiment_map = {'Positive': 'Positive', 'Pos': 'Positive', '1': 'Positive',
                             'Negative': 'Negative', 'Neg': 'Negative', '-1': 'Negative',
                             'Neutral': 'Neutral'}
            df['Sentiment_Clean'] = df['Sentiment'].map(sentiment_map).fillna('Neutral')
        else:
            df['Sentiment_Clean'] = 'Neutral'

        # تنظيف الأعمدة الأخرى
        if 'المدينة' not in df.columns: df['المدينة'] = 'غير محدد'
        if 'اسم_المنشأة' not in df.columns: df['اسم_المنشأة'] = 'غير معروف'
        if 'macro_category' not in df.columns: df['macro_category'] = 'عام'
        if 'strategic_pillar' not in df.columns: df['strategic_pillar'] = 'عام'
        if 'Date_Clean' in df.columns: df['Date_Clean'] = pd.to_datetime(df['Date_Clean'], errors='coerce')

        # دمج القطاعات
        try:
            df_cats = pd.read_excel("Saudi_CSR_Dataset.xlsx", engine='openpyxl', usecols=['نوع_النشاط', 'القطاع'])
            mapping = df_cats.drop_duplicates('نوع_النشاط').set_index('نوع_النشاط')['القطاع'].to_dict()
            df['Main_Sector'] = df['نوع_النشاط'].map(mapping).fillna(df['نوع_النشاط'])
        except:
            df['Main_Sector'] = df['نوع_النشاط']

        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty: st.stop()

# ==========================================
# 🔍 الفلاتر
# ==========================================
st.sidebar.markdown("## ⚙️ إعدادات التحليل")
cities = ['الكل'] + sorted(list(df['المدينة'].astype(str).unique()))
sel_city = st.sidebar.selectbox("🏙️ المدينة", cities)

sectors = ['الكل'] + sorted(list(df['Main_Sector'].astype(str).unique()))
sel_sector = st.sidebar.selectbox("🏢 القطاع", sectors)

df_filtered = df.copy()
if sel_city != 'الكل': df_filtered = df_filtered[df_filtered['المدينة'] == sel_city]
if sel_sector != 'الكل': df_filtered = df_filtered[df_filtered['Main_Sector'] == sel_sector]

# ==========================================
# 1️⃣ القسم الأول: الملخص والمؤشرات
# ==========================================
total = len(df_filtered)
pos = len(df_filtered[df_filtered['Sentiment_Clean'] == 'Positive'])
neg = len(df_filtered[df_filtered['Sentiment_Clean'] == 'Negative'])
satisfaction_rate = int((pos / total) * 100) if total > 0 else 0

c_title, c_gauge = st.columns([1.5, 1])
with c_title:
    st.markdown("""
        <div style='padding-top: 40px;'>
            <h1 style='font-size: 3.5rem; background: -webkit-linear-gradient(#eee, #d4af37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                نبض السوق السعودي
            </h1>
            <p style='color: #aab6fe; font-size: 1.2rem; margin-top: -10px;'>Strategic Market Intelligence Dashboard</p>
        </div>
    """, unsafe_allow_html=True)

with c_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = satisfaction_rate,
        title = {'text': "مؤشر الرضا العام", 'font': {'size': 18, 'color': "white", 'family': "Tajawal"}},
        number = {'suffix': "%", 'font': {'color': "#d4af37", 'size': 40}},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#d4af37"},
            'bgcolor': "rgba(255,255,255,0.05)",
            'steps': [{'range': [0, 50], 'color': 'rgba(231, 76, 60, 0.2)'}, {'range': [50, 100], 'color': 'rgba(80, 185, 101, 0.2)'}],
        }))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=10, l=20, r=20), height=180)
    st.plotly_chart(fig_gauge, use_container_width=True)

# بطاقات الأرقام
col1, col2, col3 = st.columns(3)
def card(label, value, color):
    return f"""<div class="glass-card"><div style="color:#ccc;">{label}</div><div class="big-number" style="color:{color}">{value}</div></div>"""
with col1: st.markdown(card("إجمالي العينة", f"{total:,}", "#fff"), unsafe_allow_html=True)
with col2: st.markdown(card("تفاعل إيجابي", f"{pos:,}", "#50b965"), unsafe_allow_html=True)
with col3: st.markdown(card("تفاعل سلبي", f"{neg:,}", "#e74c3c"), unsafe_allow_html=True)

# ==========================================
# 🆕 إضافة جديدة: مؤشرات أداء القطاعات (ديناميكي)
# ==========================================
st.markdown("---")
st.markdown("### 🏢 مؤشرات الأداء حسب القطاع")

# تجميع البيانات حسب القطاع الرئيسي
sector_perf = df_filtered.groupby('Main_Sector').apply(
    lambda x: (len(x[x['Sentiment_Clean'] == 'Positive']) / len(x) * 100) if len(x) > 0 else 0
).sort_values(ascending=False)

# لو المستخدم اختار قطاع محدد، نعرضه لوحده، لو اختار الكل نعرض أفضل 5
if sel_sector != 'الكل':
    display_sectors = sector_perf[sector_perf.index == sel_sector]
else:
    display_sectors = sector_perf.head(5)

cols = st.columns(len(display_sectors)) if len(display_sectors) > 0 else [st.container()]
for i, (sec_name, score) in enumerate(display_sectors.items()):
    color = "#50b965" if score >= 60 else ("#f1c40f" if score >= 40 else "#e74c3c")
    with cols[i]:
        st.markdown(f"""
        <div class="glass-card" style="padding: 15px;">
            <div style="font-size:0.9rem; color:#aaa; min-height:40px;">{sec_name}</div>
            <div style="font-size: 2rem; font-weight:bold; color: {color};">{int(score)}%</div>
            <div style="height: 4px; background: #333; border-radius: 2px; margin-top: 10px;">
                <div style="width: {score}%; background: {color}; height: 100%; border-radius: 2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 2️⃣ القسم الثاني: لماذا يشتكي العملاء؟ (توسيع وتوحيد الألوان)
# ==========================================
st.markdown("---")
st.markdown("### 🔍 تحليل الأسباب الجذرية (Root Cause Analysis)")

# إعدادات الألوان الموحدة (ذهبي وأخضر وأحمر)
custom_colors = ['#d4af37', '#50b965', '#e74c3c', '#f1c40f', '#3498db', '#9b59b6']
chart_config = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family='Tajawal'))

# جعل الرسوم بعرض الصفحة
row2_1, row2_2 = st.columns([1, 1])

with row2_1:
    pillar_counts = df_filtered['strategic_pillar'].value_counts().head(6)
    fig_p = px.bar(pillar_counts, x=pillar_counts.values, y=pillar_counts.index, orientation='h',
                   title="المحاور الاستراتيجية للشكاوى",
                   color_discrete_sequence=['#d4af37']) # توحيد اللون (ذهبي)
    fig_p.update_layout(**chart_config)
    st.plotly_chart(fig_p, use_container_width=True)

with row2_2:
    # نأخذ الشكاوى السلبية فقط
    neg_issues = df_filtered[df_filtered['Sentiment_Clean'] == 'Negative']['macro_category'].value_counts().head(7)
    fig_m = px.pie(values=neg_issues.values, names=neg_issues.index, title="أدق التفاصيل (Deep Dive)",
                   color_discrete_sequence=custom_colors, hole=0.4) # نفس باليت الألوان
    fig_m.update_layout(**chart_config)
    fig_m.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_m, use_container_width=True)

# ==========================================
# 3️⃣ القسم الثالث: الشبكة العنكبوتية المتقدمة (Multi-level)
# ==========================================
st.markdown("---")
st.markdown("### 🕸️ الشبكة المترابطة: (القطاع -> المنشأة -> المشكلة)")
st.caption("تحليل عميق يربط بين نوع النشاط، وأهم المنشآت فيه، وأسباب الشكاوى الخاصة بكل منشأة.")

# تجهيز البيانات للشبكة (3 مستويات)
# نأخذ عينة من البيانات السلبية
net_df = df_filtered[df_filtered['Sentiment_Clean'] == 'Negative'].head(200)

if not net_df.empty:
    G = nx.Graph()
    
    # المركز: النشاط الفرعي (القطاع)
    center_node = net_df['نوع_النشاط'].mode()[0] if not net_df.empty else "القطاع"
    G.add_node(center_node, label=center_node, color='#d4af37', size=35, title="النشاط الرئيسي") # ذهبي
    
    # المستوى 1: المنشآت (Top 10 companies in this sector)
    top_companies = net_df['اسم_المنشأة'].value_counts().head(10).index
    
    for comp in top_companies:
        # إضافة عقدة المنشأة
        G.add_node(comp, label=comp, color='#13367', size=25, title="منشأة") # أزرق غامق
        G.add_edge(center_node, comp, color='rgba(255,255,255,0.3)', width=2)
        
        # المستوى 2: مشاكل هذه المنشأة
        comp_issues = net_df[net_df['اسم_المنشأة'] == comp]['macro_category'].value_counts().head(3)
        for issue, count in comp_issues.items():
            # إضافة عقدة المشكلة (حجمها حسب التكرار)
            G.add_node(f"{comp}_{issue}", label=issue, color='#e74c3c', size=10 + (count*2), title=f"تكرار: {count}") # أحمر
            G.add_edge(comp, f"{comp}_{issue}", color='rgba(231, 76, 60, 0.4)')

    # رسم الشبكة
    nt = Network(height="600px", width="100%", bgcolor="#00000000", font_color="white") # خلفية شفافة
    nt.from_nx(G)
    
    # فيزياء الشبكة (توزيع مريح للعين)
    nt.force_atlas_2based(gravity=-80, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)
    
    # الحفظ والعرض (بدون حدود)
    try:
        nt.save_graph("network.html")
        with open("network.html", "r", encoding="utf-8") as f:
            html_string = f.read()
        # تعديل الستايل داخل HTML لإزالة الهوامش
        html_string = html_string.replace('<body>', '<body style="margin:0; padding:0; overflow:hidden;">')
        components.html(html_string, height=620, scrolling=False)
    except:
        st.error("خطأ في بناء الشبكة")
else:
    st.info("البيانات غير كافية لرسم الشبكة المتداخلة لهذا الفلتر.")

# تذييل
st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>Saudi Market Intelligence © 2026 | Powered by GenAI</div>", unsafe_allow_html=True)
