import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Ultimate Interactive Dashboard", page_icon="🌐", layout="wide")

# 2. تصميم CSS احترافي
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        .main-header { font-size: 40px; font-weight: bold; color: #00f2fe; text-align: center; margin-bottom: 10px; }
        .sub-header { font-size: 20px; color: #a8b2c1; text-align: center; margin-bottom: 30px; }
        div[data-testid="metric-container"] {
            background-color: #1e2633; border-left: 5px solid #00f2fe; 
            padding: 15px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        }
    </style>
""", unsafe_allow_html=True)

# العنوان
st.markdown('<div class="main-header">🌐 منصة التحليلات الذكية التفاعلية</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ارفع ملف بياناتك لاكتشاف الرؤى، الاتجاهات، والعلاقات بضغطة زر</div>', unsafe_allow_html=True)

# 3. القائمة الجانبية - رفع الملف
st.sidebar.header("📂 إدارة البيانات")
uploaded_file = st.sidebar.file_uploader("ارفع ملف البيانات (Excel / CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        # قراءة البيانات
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        df.columns = df.columns.str.strip() # تنظيف أسماء الأعمدة

        # استخراج أنواع الأعمدة
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # 4. فلترة تفاعلية في القائمة الجانبية
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 فلاتر البيانات")
        df_filtered = df.copy()
        if cat_cols:
            selected_filter_col = st.sidebar.selectbox("اختر عمود للفلترة:", ["بدون فلتر"] + cat_cols)
            if selected_filter_col != "بدون فلتر":
                unique_vals = df[selected_filter_col].dropna().unique().tolist()
                selected_vals = st.sidebar.multiselect(f"اختر قيم {selected_filter_col}:", unique_vals, default=unique_vals)
                df_filtered = df[df[selected_filter_col].isin(selected_vals)]

        st.sidebar.success(f"تم تحليل البيانات! (الصفوف المتبقية: {len(df_filtered)})")

        # 5. كروت المؤشرات التفاعلية (KPIs)
        st.markdown("### 📊 مؤشرات الأداء الحيوية (KPIs)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        kpi1.metric("إجمالي السجلات (الصفوف)", f"{len(df_filtered):,}")
        kpi2.metric("إجمالي الأعمدة", f"{df_filtered.shape[1]}")
        
        if num_cols:
            kpi_target = st.selectbox("اختر العمود الرقمي لحساب الإجماليات المتغيرة:", num_cols)
            total_val = df_filtered[kpi_target].sum()
            avg_val = df_filtered[kpi_target].mean()
            kpi3.metric(f"إجمالي ({kpi_target})", f"{total_val:,.2f}")
            kpi4.metric(f"متوسط ({kpi_target})", f"{avg_val:,.2f}")
        else:
            kpi3.metric("لا توجد أعمدة رقمية", "0")
            kpi4.metric("لا توجد أعمدة رقمية", "0")

        st.markdown("---")

        # 6. نظام التبويبات للتحليل الشامل (Tabs)
        tab1, tab2, tab3, tab4 = st.tabs(["📊 التحليل العام", "🔗 تحليل العلاقات", "📦 التوزيع الإحصائي", "📋 تفاصيل البيانات"])

        # التبويب الأول: التحليل العام (أعمدة ودائرة)
        with tab1:
            st.markdown("#### 📈 مقارنة الفئات وتوزيع النسب")
            col1, col2 = st.columns(2)
            with col1:
                if cat_cols and num_cols:
                    bar_x = st.selectbox("المحور الأفقي (الفئات):", cat_cols, key='bar_x')
                    bar_y = st.selectbox("المحور الرأسي (القيم):", num_cols, key='bar_y')
                    # تجميع لأعلى 15 نتيجة
                    bar_data = df_filtered.groupby(bar_x)[bar_y].sum().reset_index().sort_values(by=bar_y, ascending=False).head(15)
                    fig_bar = px.bar(bar_data, x=bar_x, y=bar_y, color=bar_y, template="plotly_dark", title=f"إجمالي {bar_y} حسب {bar_x}", color_continuousscale="Blues")
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("نحتاج لأعمدة رقمية ونصية معاً لرسم هذا المخطط.")
            
            with col2:
                if cat_cols and num_cols:
                    pie_name = st.selectbox("تصنيف الدائرة:", cat_cols, key='pie_name')
                    pie_val = st.selectbox("قيم الدائرة:", num_cols, key='pie_val')
                    pie_data = df_filtered.groupby(pie_name)[pie_val].sum().reset_index().head(10)
                    fig_pie = px.pie(pie_data, names=pie_name, values=pie_val, hole=0.4, template="plotly_dark", title=f"توزيع {pie_val} على {pie_name}")
                    st.plotly_chart(fig_pie, use_container_width=True)

        # التبويب الثاني: تحليل العلاقات (Scatter Plot)
        with tab2:
            st.markdown("#### 📍 اكتشاف العلاقات بين المؤشرات الرقمية")
            if len(num_cols) >= 2:
                sc_col1, sc_col2 = st.columns(2)
                sc_x = sc_col1.selectbox("المحور الأفقي (X):", num_cols, index=0)
                sc_y = sc_col2.selectbox("المحور الرأسي (Y):", num_cols, index=1)
                
                fig_scatter = px.scatter(df_filtered, x=sc_x, y=sc_y, color=cat_cols[0] if cat_cols else None, 
                                         template="plotly_dark", title=f"علاقة {sc_y} بـ {sc_x}", opacity=0.7)
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("نحتاج لعمودين رقميين على الأقل لرسم مخطط العلاقات (Scatter Plot).")

        # التبويب الثالث: التوزيع الإحصائي
        with tab3:
            st.markdown("#### 📦 تحليل التوزيع واكتشاف القيم الشاذة")
            if num_cols:
                dist_col = st.selectbox("اختر العمود الرقمي لتحليله:", num_cols, key='dist_col')
                fig_hist = px.histogram(df_filtered, x=dist_col, marginal="box", template="plotly_dark", 
                                        title=f"التوزيع الإحصائي والصندوقي لـ {dist_col}", color_discrete_sequence=['#00f2fe'])
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("لا توجد أعمدة رقمية للتحليل.")

        # التبويب الرابع: البيانات الخام
        with tab4:
            st.markdown("#### 📋 استعراض قاعدة البيانات الحالية")
            st.dataframe(df_filtered, use_container_width=True)
            
            # زر لتحميل البيانات المفلترة
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(label="💾 تحميل البيانات الحالية كـ CSV", data=csv, file_name="filtered_data.csv", mime="text/csv")

    except Exception as e:
        st.error(f"حدث خطأ غير متوقع أثناء معالجة البيانات: {e}")

else:
    # الشاشة الترحيبية
    st.info("👈 يرجى رفع ملفك من القائمة الجانبية. الداشبورد سيتكيف تلقائياً مع بياناتك ويعرض كافة التحليلات التفاعلية.")
