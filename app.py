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

# إعدادات الألوان الموحدة (ذهبي لامع، أخضر زمردي، وألوان متدرجة)
shiny_palette = ['#d4af37', '#50b965', '#2ecc71', '#f1c40f', '#e67e22', '#16a085']
chart_config = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family='Tajawal'))

# جعل الرسوم بعرض الصفحة
row2_1, row2_2 = st.columns([1, 1])

with row2_1:
    pillar_counts = df_filtered['strategic_pillar'].value_counts().head(6)
    fig_p = px.bar(pillar_counts, x=pillar_counts.values, y=pillar_counts.index, orientation='h',
                   title="المحاور الاستراتيجية للشكاوى",
                   # تعديل اللون إلى الذهبي الأساسي
                   color_discrete_sequence=['#d4af37'])
    fig_p.update_layout(**chart_config)
    # إضافة تأثير لمعان على البارات (حدود فاتحة وشفافية)
    fig_p.update_traces(marker_line_color='rgba(255,255,255,0.4)', marker_line_width=1, opacity=0.9)
    st.plotly_chart(fig_p, use_container_width=True)

with row2_2:
    # نأخذ الشكاوى السلبية فقط
    neg_issues = df_filtered[df_filtered['Sentiment_Clean'] == 'Negative']['macro_category'].value_counts().head(7)
    fig_m = px.pie(values=neg_issues.values, names=neg_issues.index, title="أدق التفاصيل (Deep Dive)",
                   # استخدام الباليت الذهبية والخضراء الجديدة
                   color_discrete_sequence=shiny_palette, hole=0.4)
    fig_m.update_layout(**chart_config)
    # إضافة حدود بيضاء رفيعة لإعطاء إحساس زجاجي
    fig_m.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=1)))
    st.plotly_chart(fig_m, use_container_width=True)
# ==========================================
# 3️⃣ القسم الثالث: الشبكة العنكبوتية الاحترافية (Dark Theme Network)
# ==========================================
st.markdown("---")
st.markdown("### 🕸️ الشبكة المترابطة: تحليل عميق للشكاوى")
st.caption("توضح الرسمة العلاقات بين القطاع الرئيسي، وأكثر المنشآت تلقياً للشكاوى، وأبرز أنواع المشاكل لكل منشأة مع أعدادها. (يمكنك التقريب والتحريك)")

# 1. تجهيز البيانات: نأخذ الشكاوى السلبية فقط
net_df = df_filtered[df_filtered['Sentiment_Clean'] == 'Negative']

if not net_df.empty:
    G = nx.Graph()
    
    # --- العقدة المركزية: القطاع (النشاط) ---
    # نأخذ النشاط الأكثر تكراراً في البيانات المفلترة كمركز
    center_label = net_df['نوع_النشاط'].mode()[0] if not net_df.empty else "القطاع"
    center_count = len(net_df)
    # تصميم ذهبي كبير ومميز
    G.add_node(center_label, label=f"{center_label}\n({center_count})", shape='dot', size=50,
               color={'background': '#d4af37', 'border': '#ffffff', 'highlight': {'background': '#f1c40f', 'border': '#fff'}},
               font={'size': 22, 'color': 'white', 'face': 'Tajawal', 'bold': True}, title="المركز: القطاع الرئيسي")
    
    # --- المستوى الأول: أهم المنشآت (Top Companies) ---
    # نأخذ أعلى 10 منشآت لديها شكاوى
    top_companies_series = net_df['اسم_المنشأة'].value_counts().head(10)
    
    for comp_name, comp_count in top_companies_series.items():
        # تصميم أزرق احترافي للمنشآت
        G.add_node(comp_name, label=f"{comp_name}\n({comp_count})", shape='dot', size=30,
                   color={'background': '#3498db', 'border': '#2980b9', 'highlight': {'background': '#5dade2', 'border': '#2980b9'}},
                   font={'color': 'white', 'size': 14, 'face': 'Tajawal'}, title=f"منشأة: {comp_name} (إجمالي الشكاوى: {comp_count})")
        # ربط المنشأة بالمركز (خط رمادي فاتح)
        G.add_edge(center_label, comp_name, color='#bdc3c7', width=2)
        
        # --- المستوى الثاني: أهم مشاكل هذه المنشأة (Top Issues) ---
        # نأخذ أعلى 5 مشاكل لكل منشأة
        comp_issues = net_df[net_df['اسم_المنشأة'] == comp_name]['macro_category'].value_counts().head(5)
        for issue_name, issue_count in comp_issues.items():
            node_id = f"{comp_name}_{issue_name}" # معرف فريد للعقدة
            # تصميم أحمر/برتقالي للمشاكل، حجمها يعتمد على التكرار
            G.add_node(node_id, label=f"{issue_name}\n({issue_count})", shape='dot', size=10 + issue_count,
                       color={'background': '#e74c3c', 'border': '#c0392b', 'highlight': {'background': '#ff6b6b', 'border': '#fff'}},
                       font={'color': 'white', 'size': 11, 'face': 'Tajawal'}, title=f"مشكلة: {issue_name} (تكرار: {issue_count})")
            # ربط المشكلة بالمنشأة (خط أحمر شفاف)
            G.add_edge(comp_name, node_id, color='rgba(231, 76, 60, 0.5)', width=1)

    # 2. إعداد الشبكة (تحديد الخلفية الداكنة والخطوط البيضاء)
    nt = Network(height="700px", width="100%", bgcolor="#0b1013", font_color="white")
    nt.from_nx(G)
    
    # 3. ضبط الفيزياء (للحصول على توزيع متباعد وجميل مثل الصورة)
    nt.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 150,
          "springConstant": 0.08,
          "damping": 0.4,
          "avoidOverlap": 1
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based"
      },
      "interaction": { "hover": true, "zoomView": true }
    }
    """)
    
    # 4. الحفظ والعرض (بدون هوامش)
    try:
        path = "network_pro.html"
        nt.save_graph(path)
        with open(path, "r", encoding="utf-8") as f:
            html_string = f.read()
        
        # إزالة هوامش صفحة الويب الداخلية
        html_string = html_string.replace('<body>', '<body style="margin:0; padding:0; overflow:hidden;">')
        
        # عرض الشبكة
        components.html(html_string, height=720, scrolling=False)
        
    except Exception as e:
        st.error(f"حدث خطأ تقني أثناء رسم الشبكة: {e}")
else:
    st.info("⚠️ لا توجد بيانات شكاوى سلبية كافية في الفلتر الحالي لرسم الشبكة التفصيلية.")
