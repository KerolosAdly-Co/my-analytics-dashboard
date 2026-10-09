import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. إعدادات الصفحة
st.set_page_config(page_title="لوحة تحكم مبيعات محل ملابس", layout="wide", page_icon="🛍️")

# ==========================================
# 2. دالة قراءة البيانات (تم تعديلها لتناسب ملفك)
# ==========================================
@st.cache_data
def load_data():
    try:
        # استخدام header=1 لتخطي الصف الأول (العنوان المدمج) واعتبار الصف الثاني هو الترويسة
        df = pd.read_excel("Sales Shop.xlsx", header=1)
        
        # تنظيف أسماء الأعمدة من المسافات
        df.columns = df.columns.str.strip()
        
        # تحويل التاريخ وحذف صف "الإجمالي" والصفوف الفارغة تلقائياً
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        df = df.dropna(subset=['التاريخ']) 
        
        # التأكد من أن الأعمدة الرقمية أرقام (ولو مش موجودة نضعها 0)
        cols_to_numeric = ['المبيعات', 'الأرباح', 'الطلبات']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
                st.warning(f"⚠️ تنبيه: العمود '{col}' غير موجود في الملف، تم تعيينه كـ 0.")
        
        # التأكد من الأعمدة النصية
        for col in ['الفرع', 'المنطقة', 'المنتج', 'الفئة']:
            if col not in df.columns:
                df[col] = 'غير محدد'
        
        # أعمدة مساعدة للتحليل
        df['الشهر'] = df['التاريخ'].dt.strftime('%Y-%m')
        df['السنة'] = df['التاريخ'].dt.year
        df['نسبة الربح'] = np.where(df['المبيعات'] > 0, (df['الأرباح'] / df['المبيعات']) * 100, 0)
        
        return df
        
    except FileNotFoundError:
        st.error("⚠️ خطأ: لم يتم العثور على ملف 'Sales Shop.xlsx'. يرجى التأكد من وجود الملف في نفس المجلد.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ حدث خطأ أثناء قراءة الملف: {e}")
        st.stop()

df = load_data()

# ==========================================
# 3. الشريط الجانبي (الفلاتر)
# ==========================================
st.sidebar.header("🔍 خيارات التصفية")
min_date = df['التاريخ'].min().date()
max_date = df['التاريخ'].max().date()
date_range = st.sidebar.date_input("اختر الفترة الزمنية", [min_date, max_date])

branches = df['الفرع'].dropna().unique() if 'الفرع' in df.columns else []
selected_branch = st.sidebar.multiselect("اختر الفرع", options=branches, default=branches)

categories = df['الفئة'].dropna().unique() if 'الفئة' in df.columns else []
selected_category = st.sidebar.multiselect("اختر الفئة", options=categories, default=categories)

# تطبيق الفلاتر
mask = (df['التاريخ'].dt.date >= date_range[0]) & (df['التاريخ'].dt.date <= date_range[1])
if selected_branch: mask = mask & (df['الفرع'].isin(selected_branch))
if selected_category: mask = mask & (df['الفئة'].isin(selected_category))
filtered_df = df[mask]

# ==========================================
# 4. عنوان اللوحة والمؤشرات الرئيسية (KPIs)
# ==========================================
st.title("🛍️ لوحة تحكم مبيعات محل الملابس")

if filtered_df.empty:
    st.warning("لا توجد بيانات متاحة للفلاتر المحددة.")
    st.stop()

total_sales = filtered_df['المبيعات'].sum()
total_profit = filtered_df['الأرباح'].sum()
total_orders = filtered_df['الطلبات'].sum()
aov = total_sales / total_orders if total_orders > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("إجمالي المبيعات", f"${total_sales:,.0f}")
col2.metric("إجمالي الأرباح", f"${total_profit:,.0f}")
col3.metric("عدد الطلبات", f"{total_orders:,.0f}")
col4.metric("متوسط قيمة الطلب (AOV)", f"${aov:,.2f}")

st.markdown("---")

# ==========================================
# 5. تقسيم اللوحة إلى تبويبات (Tabs)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 نظرة عامة والأرباح السنوية", "🏢 تحليل الفروع والأرباح الشهرية", "📦 تحليل المنتجات"])

# ==========================================
# التبويب الأول: نظرة عامة (Overview & Yearly Profit)
# ==========================================
with tab1:
    st.subheader("📈 تطور المبيعات والأرباح")
    trend_data = filtered_df.groupby('التاريخ')[['المبيعات', 'الأرباح']].sum().reset_index()
    fig_trend = px.line(trend_data, x='التاريخ', y=['المبيعات', 'الأرباح'], 
                        color_discrete_map={'المبيعات': '#2ecc71', 'الأرباح': '#3498db'},
                        labels={'value': 'المبلغ ($)', 'variable': 'المؤشر'})
    st.plotly_chart(fig_trend, use_container_width=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fig_pie = px.pie(filtered_df, names='الفئة', values='المبيعات', hole=0.4, title="المبيعات حسب الفئة")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_t2:
        fig_tree = px.treemap(filtered_df, path=['الفئة', 'المنتج'], values='المبيعات', 
                              title="التسلسل الهرمي للمبيعات (فئة -> منتج)")
        st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("---")
    st.subheader("📅 تحليل الأرباح السنوية (أكثر سنة ربحاً)")
    
    yearly_profit = filtered_df.groupby('السنة')['الأرباح'].sum().reset_index()
    if not yearly_profit.empty:
        best_year_idx = yearly_profit['الأرباح'].idxmax()
        best_year = yearly_profit.loc[best_year_idx]
        
        col_y1, col_y2 = st.columns([1, 2])
        with col_y1:
            st.metric(label="🏆 أكثر سنة كان فيها ربح", 
                      value=f"سنة {int(best_year['السنة'])}", 
                      delta=f"${best_year['الأرباح']:,.2f}")
        with col_y2:
            fig_year = px.bar(yearly_profit, x='السنة', y='الأرباح', 
                              title="إجمالي الأرباح لكل سنة",
                              text_auto='.2s', color='الأرباح', color_continuous_scale='Greens')
            st.plotly_chart(fig_year, use_container_width=True)

# ==========================================
# التبويب الثاني: تحليل الفروع (Branch Analysis & Monthly Profit)
# ==========================================
with tab2:
    st.subheader("🏢 أداء الفروع (أي فرع يبيع أكثر؟)")
    
    branch_region_sales = filtered_df.groupby(['الفرع', 'المنطقة'])['المبيعات'].sum().reset_index()
    fig_branch_bar = px.bar(branch_region_sales, x='الفرع', y='المبيعات', color='المنطقة',
                            title="مبيعات الفروع موزعة حسب المنطقة", text_auto='.2s',
                            color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_branch_bar.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_branch_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("💰 صافي الربح الشهري لكل فرع")
    st.markdown("يوضح الرسم البياني التالي كم يكسبك كل فرع على حدة في كل شهر.")
    
    # إنشاء جدول محوري (Pivot Table) للأرباح الشهرية لكل فرع
    monthly_branch_profit = filtered_df.pivot_table(index='الشهر', columns='الفرع', values='الأرباح', aggfunc='sum').fillna(0)
    
    if not monthly_branch_profit.empty:
        fig_monthly_profit = px.line(monthly_branch_profit, x=monthly_branch_profit.index, y=monthly_branch_profit.columns,
                                     title="تطور الأرباح الشهرية لكل فرع",
                                     labels={'value': 'الأرباح ($)', 'variable': 'الفرع', 'الشهر': 'الشهر'})
        st.plotly_chart(fig_monthly_profit, use_container_width=True)
        
        with st.expander("📄 عرض جدول الأرباح الشهرية لكل فرع"):
            st.dataframe(monthly_branch_profit.style.format("{:,.2f}"), use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 تحليل منتجات فرع معين")
    selected_branch_drill = st.selectbox("اختر فرعاً لعرض المنتجات التي باعها:", options=filtered_df['الفرع'].unique())
    
    if selected_branch_drill:
        branch_products = filtered_df[filtered_df['الفرع'] == selected_branch_drill].groupby('المنتج')['المبيعات'].sum().nlargest(10).reset_index()
        fig_branch_products = px.bar(branch_products, x='المبيعات', y='المنتج', orientation='h',
                                     title=f"أفضل 10 منتجات مبيعاً في فرع: {selected_branch_drill}",
                                     color='المبيعات', color_continuous_scale='Teal')
        fig_branch_products.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_branch_products, use_container_width=True)

# ==========================================
# التبويب الثالث: تحليل المنتجات (Product Analysis)
# ==========================================
with tab3:
    st.subheader("📦 الإجمالي لصنف معين في الفروع كلها")
    
    selected_product = st.selectbox("اختر منتجاً لمعرفة إجمالي مبيعاته في كل فرع:", options=filtered_df['المنتج'].unique())
    
    if selected_product:
        product_df = filtered_df[filtered_df['المنتج'] == selected_product]
        product_branch_sales = product_df.groupby('الفرع')['المبيعات'].sum().reset_index()
        
        col_pr1, col_pr2 = st.columns([1, 2])
        with col_pr1:
            st.metric("إجمالي مبيعات الصنف في كل الفروع", f"${product_branch_sales['المبيعات'].sum():,.2f}")
            st.metric("عدد القطع المباعة", f"{product_df['الطلبات'].sum():,.0f}")
        with col_pr2:
            fig_product_branch = px.bar(product_branch_sales, x='الفرع', y='المبيعات', 
                                         title=f"مبيعات '{selected_product}' في كل فرع",
                                         color='المبيعات', color_continuous_scale='Bluyl', text_auto='.2s')
            st.plotly_chart(fig_product_branch, use_container_width=True)

    st.markdown("---")
    st.subheader("🏆 أداء المنتجات العام")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        top_sales = filtered_df.groupby('المنتج')['المبيعات'].sum().nlargest(5).reset_index()
        fig_top_sales = px.bar(top_sales, x='المبيعات', y='المنتج', orientation='h', 
                               title="أفضل 5 منتجات مبيعاً", color='المبيعات', color_continuous_scale='Blues')
        fig_top_sales.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_top_sales, use_container_width=True)

    with col_p2:
        top_profit = filtered_df.groupby('المنتج')['الأرباح'].sum().nlargest(5).reset_index()
        fig_top_profit = px.bar(top_profit, x='الأرباح', y='المنتج', orientation='h', 
                                title="أفضل 5 منتجات ربحية", color='الأرباح', color_continuous_scale='Greens')
        fig_top_profit.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_top_profit, use_container_width=True)

    with col_p3:
        profit_margin = filtered_df.groupby('المنتج')['نسبة الربح'].mean().nlargest(5).reset_index()
        fig_margin = px.bar(profit_margin, x='نسبة الربح', y='المنتج', orientation='h',
                            title="أعلى 5 منتجات في نسبة الربح (%)", color='نسبة الربح', color_continuous_scale='Purples')
        fig_margin.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_margin, use_container_width=True)

# ==========================================
# 10. جدول البيانات التفصيلي
# ==========================================
with st.expander("📄 عرض البيانات التفصيلية (Sales Shop.xlsx)"):
    st.dataframe(filtered_df.sort_values(by='التاريخ', ascending=False), use_container_width=True)
