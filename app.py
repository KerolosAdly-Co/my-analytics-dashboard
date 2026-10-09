import streamlit as st
import pandas as pd
import plotly.express as px

# إعدادات الصفحة
st.set_page_config(
    page_title="لوحة تحكم مبيعات الشركات",
    page_icon="📈",
    layout="wide"
)

# تصميم الشعار والعنوان المطلوب
st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #1f4068, #162447); border-radius: 10px; color: white; margin-bottom: 25px;'>
        <h1 style='margin: 0; font-size: 32px;'>📈 لوحة تحليل مبيعات الشركات الذكية</h1>
        <p style='margin-top: 10px; font-size: 18px; color: #e4e4e4;'>ارفع ملف الاكسل الخاص بك لرؤية المبيعات</p>
    </div>
""", unsafe_allow_html=True)

# القائمة الجانبية لرفع الملف
st.sidebar.header("📁 رفع بيانات المبيعات")
uploaded_file = st.sidebar.file_uploader("اختر ملف الاكسل (Excel / CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        # قراءة الملف حسب نوعه
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # تنظيف أسماء الأعمدة (إزالة الفراغات)
        df.columns = df.columns.str.strip()

        st.sidebar.success("تم تحليل بيانات المبيعات بنجاح! 🚀")

        # محاولة اكتشاف الأعمدة الذكية تلقائياً للمبيعات والتاريخ والمنتجات
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # مؤشرات الأداء الرئيسية (KPIs)
        st.subheader("📊 مؤشرات الأداء العامة")
        col1, col2, col3, col4 = st.columns(4)
        
        total_rows = df.shape[0]
        col1.metric("إجمالي العمليات / السجلات", f"{total_rows:,}")
        
        if numeric_cols:
            # افتراض أول عمود رقمي كمؤشر للمبيعات أو القيمة
            main_metric = numeric_cols[0]
            total_sales = df[main_metric].sum()
            avg_sales = df[main_metric].mean()
            col2.metric(f"إجمالي {main_metric}", f"{total_sales:,.2f}")
            col3.metric(f"متوسط {main_metric}", f"{avg_sales:,.2f}")
        else:
            col2.metric("إجمالي الأعمدة الرقمية", "0")
            col3.metric("متوسط المبيعات", "غير متوفر")

        col4.metric("عدد أعمدة البيانات", df.shape[1])

        st.markdown("---")

        # الرسوم البيانية الاحترافية للمبيعات
        st.subheader("📉 تحليلات ورسوم المبيعات البيانية")
        
        c1, c2 = st.columns(2)

        with c1:
            if text_cols and numeric_cols:
                x_col = st.selectbox("اختر فئة التحليل (مثل: المنتجات، العملاء، الفروع):", text_cols, key='x_axis')
                y_col = st.selectbox("اختر عمود القيمة المالية أو المبيعات:", numeric_cols, key='y_axis')
                
                # تجميع البيانات لعرض أفضل 10 نتائج
                grouped_df = df.groupby(x_col)[y_col].sum().reset_index().sort_values(by=y_col, ascending=False).head(10)
                
                fig_bar = px.bar(
                    grouped_df, x=x_col, y=y_col, 
                    title=f"أعلى 10 حسب {y_col} لكل {x_col}",
                    template="plotly_dark",
                    color=y_col,
                    color_continuousscale="blues"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("يلزم وجود أعمدة نصية وأعمدة رقمية لعرض الرسوم البيانية للمقارنة.")

        with c2:
            if numeric_cols:
                pie_col = st.selectbox("اختر عموداً رقمياً لتوزيع النسب:", numeric_cols, key='pie_axis')
                if text_cols:
                    pie_cat = st.selectbox("اختر عمود التصنيف الدائري:", text_cols, key='pie_cat')
                    pie_data = df.groupby(pie_cat)[pie_col].sum().reset_index().head(7)
                    
                    fig_pie = px.pie(
                        pie_data, names=pie_cat, values=pie_col,
                        title=f"توزيع نسب {pie_col} حسب {pie_cat}",
                        template="plotly_dark",
                        hole=0.4
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("يتطلب رسوم التوزيع الدائري وجود أعمدة نصية بجانب الأعمدة الرقمية.")

        # استعراض جدول البيانات الكامل
        st.markdown("---")
        st.subheader("📋 جدول بيانات المبيعات التفصيلي")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة ملف الإكسيل: {e}")
else:
    st.info("👈 يرجى رفع ملف الاكسل أو الـ CSV من القائمة الجانبية للبدء في استعراض لوحة مبيعاتك.")
