import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Ultimate Analytics Dashboard", page_icon="📊", layout="wide")

st.title("🚀 المنصة الشاملة للتحليل الذكي")
st.markdown("ارفع ملف البيانات الخاص بك (`CSV` أو `Excel`) لاستعراض التحليلات فوراً.")

st.sidebar.header("📁 إدارة البيانات")
uploaded_file = st.sidebar.file_uploader("اختر ملف البيانات", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.sidebar.success("تم رفع قراءة البيانات بنجاح!")
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("إجمالي الصفوف", f"{df.shape[0]:,}")
        kpi2.metric("إجمالي الأعمدة", df.shape[1])
        kpi3.metric("القيم المفقودة", int(df.isna().sum().sum()))
        kpi4.metric("الأعمدة الرقمية", len(numeric_cols))

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 التوزيعات والإحصاء", "🏆 المقارنات والفئات", "📋 استعراض البيانات"])

        with tab1:
            st.subheader("تحليل التوزيع الإحصائي")
            if numeric_cols:
                selected_num = st.selectbox("اختر عموداً رقمياً:", numeric_cols)
                fig = px.histogram(df, x=selected_num, marginal="box", template="plotly_dark", title=f"التوزيع لـ {selected_num}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("لا توجد أعمدة رقمية.")

        with tab2:
            st.subheader("مقارنة الفئات")
            if categorical_cols and numeric_cols:
                cat_col = st.selectbox("عمود الفئات:", categorical_cols)
                num_col = st.selectbox("القياس الرقمي:", numeric_cols, key='num_comp')
                
                agg_df = df.groupby(cat_col)[num_col].sum().reset_index()
                fig_bar = px.bar(agg_df.head(15), x=cat_col, y=num_col, template="plotly_dark", title=f"إجمالي {num_col} لكل {cat_col}")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("يلزم وجود أعمدة نصية ورقمية معاً.")

        with tab3:
            st.subheader("البيانات الخام")
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
else:
    st.info("👈 يرجى رفع ملف بيانات من القائمة الجانبية للبدء.")