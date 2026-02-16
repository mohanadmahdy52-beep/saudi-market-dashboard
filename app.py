import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import streamlit.components.v1 as components
import networkx as nx

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Saudi Market Pulse", page_icon="💎")

# ==========================================
# 🎨 التصميم السينمائي الفاخر (Dark Luxury Return)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Tajawal:wght@300;400;700;900&display=swap');

    /* خلفية داكنة فخمة ثابتة */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Tajawal', sans-serif;
    }

    /* العناوين الذهبية */
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
    
    .big-number {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        font-weight: bold;
        color: #fff;
    }
    
    /* القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.98);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* إخفاء الهوامش العلوية */
    .block-container { padding-top: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 📥 تحميل ودمج البيانات (Data Integration)
# ==========================================
@st.cache_data
def load_data():
    try:
        # 1. تحميل الملف الرئيسي (15,000 صف)
        df_master = pd.read_excel("Saudi_CSR_MASTER_FILE_Final_Fixed.xlsx", engine='openpyxl', nrows=15000)
        
        # 2. تحميل ملف التصنيف (القطاعات)
        try:
            df_cats = pd.read_excel("Saudi_CSR_Dataset.xlsx", engine='openpyxl', usecols=['نوع_النشاط', 'القطاع'])
            # حذف التكرار لإنشاء قاموس (نوع النشاط -> القطاع)
            sector_map = df_cats.drop_duplicates('نوع_النشاط').set_index('نوع_النشاط')['القطاع'].to_dict()
            # تطبيق المابينج
            df_master['Main_Sector'] = df_master['نوع_النشاط'].map(sector_map).fillna('قطاعات أخرى')
        except:
            df_master['Main_Sector'] = 'عام' # لو الملف التاني مش موجود

        # 3. معالجة التاريخ والأرقام
        if 'Date_Clean' in df_master.columns:
            df_master['Date_Clean'] = pd.to_datetime(df_master['Date_Clean'], errors='coerce')

        # 4. معالجة التقييم (Score & Sentiment)
        # البحث عن عمود السكور أياً كان اسمه
        score_col = None
        for col in ['Sentiment_Score', 'Score', 'score', 'sentiment_score']:
            if col in df_master.columns:
                score_col = col
                break
        
        if score_col:
            df_master['Final_Score'] = pd.to_numeric(df_master[score_col], errors='coerce').fillna(0)
            # إعادة حساب المشاعر لضمان الدقة
            df_master['Sentiment'] = df_master['Final_Score'].apply(
                lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral')
            )
        else:
            df_master['Final_Score'] = 0
            df_master['Sentiment'] = 'Neutral'

        # 5. تصنيف المناطق (Mapping from City)
        regions_map = {
            'Riyadh': 'الوسطى', 'الرياض': 'الوسطى',
            'Jeddah': 'الغربية', 'جدة': 'الغربية', 'Mecca': 'الغربية', 'مكة': 'الغربية', 'Medina': 'الغربية', 'المدينة': 'الغربية',
            'Dammam': 'الشرقية', 'الدمام': 'الشرقية', 'Khobar': 'الشرقية', 'الخبر': 'الشرقية',
            'Abha': 'الجنوبية', 'أبها': 'الجنوبية', 'Jazan': 'الجنوبية', 'جازان': 'الجنوبية',
            'Tabuk': 'الشمالية', 'تبوك': 'الشمالية', 'Hail': 'الشمالية', 'حائل': 'الشمالية'
        }
        if 'المدينة' in df_master.columns:
            df_master['Region'] = df_master['المدينة'].map(regions_map).fillna('أخرى')
        else:
            df_master['Region'] = 'غير محدد'

        return df_master
    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
        return pd.DataFrame()

# تنفيذ التحميل
with st.spinner('جاري دمج البيانات وتحليل العلاقات...'):
    df = load_data()

if df.empty:
    st.stop()

# ==========================================
# 🔍 القائمة الجانبية (الفلاتر)
# ==========================================
st.sidebar.markdown("### ⚙️ إعدادات التحليل")

# فلتر المنطقة
regions = ['الكل'] + sorted(list(df['Region'].unique()))
sel_region = st.sidebar.selectbox("🗺️ المنطقة", regions)

# فلتر القطاع الرئيسي (من الملف الثاني)
main_sectors = ['الكل'] + sorted(list(df['Main_Sector'].unique()))
sel_main_sector = st.sidebar.selectbox("🏢 القطاع الرئيسي", main_sectors)

# فلتر نوع النشاط الفرعي
sub_sectors = ['الكل'] + sorted(list(df['نوع_النشاط'].unique()))
sel_sub_sector = st.sidebar.selectbox("🔧 النشاط الفرعي", sub_sectors)

# تطبيق الفلترة
df_filtered = df.copy()
if sel_region != 'الكل':
    df_filtered = df_filtered[df_filtered['Region'] == sel_region]
if sel_main_sector != 'الكل':
    df_filtered = df_filtered[df_filtered['Main_Sector'] == sel_main_sector]
if sel_sub_sector != 'الكل':
    df_filtered = df_filtered[df_filtered['نوع_النشاط'] == sel_sub_sector]

# ==========================================
# 🌟 القسم العلوي: المؤشرات (Hero Section)
# ==========================================

# حساب الأرقام الحقيقية
total_rev = len(df_filtered)
pos_rev = len(df_filtered[df_filtered['Sentiment'] == 'Positive'])
neg_rev = len(df_filtered[df_filtered['Sentiment'] == 'Negative'])
satisfaction = int((pos_rev / total_rev * 100)) if total_rev > 0 else 0

st.markdown(f"""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='font-size: 3.5rem; background: -webkit-linear-gradient(#eee, #d4af37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            نبض السوق السعودي
        </h1>
        <p style='color: #888; font-size: 1.1rem;'>Strategic Market Intelligence Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# عرض الكروت
c1, c2, c3, c4 = st.columns(4)
def card(label, value, color="#fff"):
    return f"""
    <div class="glass-card">
        <div style="color: #aab6fe; font-size: 0.9rem;">{label}</div>
        <div class="big-number" style="color: {color}">{value}</div>
    </div>
    """

with c1: st.markdown(card("إجمالي البيانات", f"{total_rev:,}"), unsafe_allow_html=True)
with c2: st.markdown(card("مؤشر الرضا العام", f"{satisfaction}%", "#d4af37"), unsafe_allow_html=True)
with c3: st.markdown(card("تفاعل إيجابي", f"{pos_rev:,}", "#50b965"), unsafe_allow_html=True)
with c4: st.markdown(card("تفاعل سلبي", f"{neg_rev:,}", "#ff6b6b"), unsafe_allow_html=True)

# ==========================================
# 📊 مؤشرات القطاعات (Barometer Style)
# ==========================================
st.markdown("### 🏢 مؤشرات الأداء حسب القطاع الرئيسي")

# تجميع البيانات حسب القطاع الرئيسي
sector_perf = df_filtered.groupby('Main_Sector')['Final_Score'].mean().sort_values(ascending=False).head(5)

cols = st.columns(len(sector_perf))
for i, (sec_name, score) in enumerate(sector_perf.items()):
    # تحويل السكور (-1 إلى 1) لنسبة (0 إلى 100)
    pct = int((score + 1) / 2 * 100)
    color = "#50b965" if pct >= 60 else ("#f1c40f" if pct >= 40 else "#e74c3c")
    
    with cols[i]:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:0.8rem; color:#ccc; height:40px;">{sec_name}</div>
            <div style="font-size: 1.8rem; font-weight:bold; color: {color};">{pct}%</div>
            <div style="height: 5px; background: #333; border-radius: 5px; margin-top: 5px;">
                <div style="width: {pct}%; background: {color}; height: 100%; border-radius: 5px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 📈 الرسوم والتحليلات
# ==========================================
st.markdown("---")
chart_config = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="Tajawal"))

col_main1, col_main2 = st.columns([2, 1])

with col_main1:
    st.markdown("### 📈 المسار الزمني (Trend)")
    if 'Date_Clean' in df_filtered.columns:
        trend = df_filtered.groupby(df_filtered['Date_Clean'].dt.to_period('M'))['Final_Score'].mean().reset_index()
        trend['Date_Clean'] = trend['Date_Clean'].astype(str)
        fig_trend = px.area(trend, x='Date_Clean', y='Final_Score', color_discrete_sequence=['#d4af37'])
        fig_trend.update_layout(**chart_config)
        st.plotly_chart(fig_trend, use_container_width=True)

with col_main2:
    st.markdown("### 🎭 توزيع المشاعر")
    fig_donut = px.donut(df_filtered, names='Sentiment', color='Sentiment', 
                         color_discrete_map={'Positive':'#50b965', 'Negative':'#ff6b6b', 'Neutral':'#888'}, hole=0.6)
    fig_donut.update_layout(**chart_config, showlegend=False)
    fig_donut.add_annotation(text=f"{satisfaction}%", showarrow=False, font=dict(size=25, color="white"))
    st.plotly_chart(fig_donut, use_container_width=True)

# ==========================================
# 🕸️ التحليل الشبكي الحقيقي (Real Network Graph)
# ==========================================
st.markdown("---")
st.markdown("### 🕸️ شبكة ترابط المشاكل (Network Analysis)")
st.caption("تحليل العلاقات بين القطاعات وبين أنواع الشكاوى (Nodes & Edges)")

# تجهيز بيانات الشبكة: نربط (القطاع) -> (المشكلة)
# نأخذ عينة من البيانات السلبية فقط
net_df = df_filtered[df_filtered['Sentiment'] == 'Negative'].head(150)

if not net_df.empty and 'macro_category' in net_df.columns:
    G = nx.Graph()
    
    # إضافة العقد والروابط
    for i, row in net_df.iterrows():
        source = row['نوع_النشاط']
        target = row['macro_category'] # تأكد أن هذا العمود موجود في الإكسل
        
        # عقدة القطاع (أزرق)
        G.add_node(source, label=source, title=source, color='#13367', size=25, group='sector')
        # عقدة المشكلة (أحمر)
        G.add_node(target, label=target, title=target, color='#e74c3c', size=15, group='problem')
        # الرابط
        G.add_edge(source, target, color='rgba(255,255,255,0.2)')

    # إعدادات الشبكة الفيزيائية
    nt = Network(height="600px", width="100%", bgcolor="#0f2027", font_color="white")
    nt.from_nx(G)
    nt.force_atlas_2based() # خوارزمية التوزيع (مثل الصورة)
    
    # حفظ وعرض
    try:
        nt.save_graph("network.html")
        with open("network.html", "r", encoding="utf-8") as f:
            html_string = f.read()
        components.html(html_string, height=620)
    except:
        st.error("خطأ في إنشاء ملف الشبكة")
else:
    st.info("لا توجد بيانات كافية لرسم الشبكة، أو عمود 'macro_category' مفقود.")

# تذييل
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Saudi Market Intelligence © 2026</div>", unsafe_allow_html=True)
