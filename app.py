import streamlit as st
import numpy as np
import pandas as pd
from millify import millify
from streamlit_extras.metric_cards import style_metric_cards
import plotly.graph_objects as go
import plotly.express as px  # تمت الإضافة لعرض الخريطة
import altair as alt

# إعداد الصفحة
st.set_page_config(page_title="Superstore Sales Analytics", page_icon="📈", layout="wide", initial_sidebar_state='collapsed')

# تعديل الـ CSS لدعم الوضع الداكن وإنزال العنوان قليلاً
st.markdown("""
        <style>
               .block-container {
                    padding-top: 4rem; 
                    padding-bottom: 1rem;
                }
                /* إزالة الخلفية البيضاء من بطاقات المؤشرات لتتوافق مع الوضع الداكن */
                div[data-testid="metric-container"] {
                    background-color: transparent;
                }
        </style>
        """, unsafe_allow_html=True) 

# دالة حساب نسبة التغير السنوية
def get_per_year_change(col, df, metric):
    grp_years = df.groupby('year')[col].agg([metric])[metric]
    grp_years = grp_years.pct_change() * 100
    grp_years.fillna(0, inplace=True)
    grp_years = grp_years.apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else 'NaN')
    return grp_years

# تحميل البيانات وتخزينها مؤقتاً
@st.cache_data(ttl=50)
def load_data():
    try:
        df = pd.read_excel(
            'Sample - Superstore.xls', 
            sheet_name=0,
            parse_dates=['Order Date', 'Ship Date']
        )
        # تنظيف أسماء الأعمدة من أي مسافات زائدة
        df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف الإكسل: {e}")
        st.stop()

    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')
    df = df.dropna(subset=['Order Date', 'Ship Date'])

    # استخراج السنة والشهر
    df['year'] = df['Order Date'].dt.year
    df['month'] = df['Order Date'].dt.to_period('M').astype(str)
    df['days to ship'] = abs((df['Ship Date'] - df['Order Date']).dt.days)

    grp_years_sales = get_per_year_change('Sales', df, 'sum')
    grp_year_profit = get_per_year_change('Profit', df, 'sum')
    grp_year_orders = get_per_year_change('Order ID', df, 'count')

    return df, grp_years_sales, grp_year_profit, grp_year_orders

# تجهيز الحاويات
sidebar = st.sidebar
dash_1 = st.container()
dash_2 = st.container()
dash_3 = st.container()
dash_4 = st.container()
dash_5 = st.container()
dash_6 = st.container()
dash_7 = st.container() # تمت إضافة قسم جديد للخريطة

# تحميل البيانات
df_original, grp_years_sales, grp_year_profit, grp_year_orders = load_data()

# الشريط الجانبي للفلترة
with sidebar:
    year_list = grp_years_sales.index.to_list()
    year_list.insert(0, "All")
    selected_year = st.selectbox("Select a year", year_list)

    if selected_year == "All":
        df = df_original
    else:
        df = df_original[df_original['year'] == int(selected_year)]

# القسم 1: العنوان
with dash_1:
    st.markdown("<h2 style='text-align: center;'>Superstore Sales Dashboard</h2>", unsafe_allow_html=True)
    st.write("")

# القسم 2: المؤشرات الرئيسية (KPIs)
with dash_2:
    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    total_orders = df['Order ID'].nunique()

    if selected_year == "All":
        sales_per_change = grp_years_sales.iloc[-1] if not grp_years_sales.empty else "0%"
        profit_per_change = grp_year_profit.iloc[-1] if not grp_year_profit.empty else "0%"
        order_count_per_change = grp_year_orders.iloc[-1] if not grp_year_orders.empty else "0%"
    else:
        sales_per_change = grp_years_sales.get(selected_year, "0%")
        profit_per_change = grp_year_profit.get(selected_year, "0%")
        order_count_per_change = grp_year_orders.get(selected_year, "0%")

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Sales", value="$" + millify(total_sales, precision=2), delta=sales_per_change)
    col2.metric(label="Profit", value="$" + millify(total_profit, precision=2), delta=profit_per_change)
    col3.metric(label="Orders", value=total_orders, delta=order_count_per_change)
    
    style_metric_cards(border_left_color="#DBF227")

# القسم 3: اتجاهات المبيعات والأرباح الشهرية
with dash_3:
    st.markdown("### 📈 Sales & Profit Trends Over Time")
    monthly_data = df.groupby('month')[['Sales', 'Profit']].sum().reset_index()
    monthly_data = monthly_data.sort_values('month')
    
    monthly_melted = monthly_data.melt('month', var_name='Metric', value_name='Amount')

    trend_chart = alt.Chart(monthly_melted).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X('month:N', title='Month', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Amount:Q', title='Amount ($)'),
        color=alt.Color('Metric:N', scale=alt.Scale(domain=['Sales', 'Profit'], range=['#9FC131', '#005C53'])),
        tooltip=['month', 'Metric', alt.Tooltip('Amount:Q', format='$,.2f')]
    ).properties(height=350, title="Monthly Sales & Profit Trends")
    
    st.altair_chart(trend_chart, use_container_width=True, theme="streamlit")

# القسم 4: أعلى 10 منتجات مبيعاً وربحاً
with dash_4:
    col1, col2 = st.columns(2)
    top_product_sales = df.groupby('Product Name')['Sales'].sum().nlargest(10).reset_index()
    top_product_profit = df.groupby('Product Name')['Profit'].sum().nlargest(10).reset_index()
    
    with col1:
        chart = alt.Chart(top_product_sales).mark_bar(opacity=0.9, color="#9FC131").encode(
            x='sum(Sales):Q',
            y=alt.Y('Product Name:N', sort='-x')   
        )
        chart = chart.properties(title="Top 10 Selling Products")
        st.altair_chart(chart, use_container_width=True, theme="streamlit")
        
    with col2:
        chart = alt.Chart(top_product_profit).mark_bar(opacity=0.9, color="#9FC131").encode(
            x='sum(Profit):Q',
            y=alt.Y('Product Name:N', sort='-x')
        )
        chart = chart.properties(title="Top 10 Most Profitable Products")
        st.altair_chart(chart, use_container_width=True, theme="streamlit")

# القسم 5: تحليل العملاء والمناطق والشحن (مع البحث الذكي عن العمود الجغرافي)
with dash_5:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Segment' in df.columns:
            segment_data = df.groupby('Segment')['Sales'].sum().reset_index()
            donut = alt.Chart(segment_data).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Sales", type="quantitative"),
                color=alt.Color(field="Segment", type="nominal", scale=alt.Scale(scheme='tableau10')),
                tooltip=['Segment', alt.Tooltip('Sales:Q', format='$,.2f')]
            ).properties(title="Sales by Customer Segment", height=300)
            st.altair_chart(donut, use_container_width=True, theme="streamlit")
        else:
            st.warning("⚠️ عمود 'Segment' غير موجود في ملف الإكسل.")

    with col2:
        # البحث التلقائي عن العمود الجغرافي المناسب (State أو Region أو Province أو City)
        geo_col = None
        for col in ['State', 'state', 'Region', 'Province', 'City']:
            if col in df.columns:
                geo_col = col
                break
        
        if geo_col:
            state_data = df.groupby(geo_col)['Sales'].sum().nlargest(10).reset_index()
            bar_state = alt.Chart(state_data).mark_bar(color="#042940").encode(
                x=alt.X('Sales:Q', axis=alt.Axis(format='~s')),
                y=alt.Y(f'{geo_col}:N', sort='-x'),
                tooltip=[geo_col, alt.Tooltip('Sales:Q', format='$,.2f')]
            ).properties(title=f"Top 10 {geo_col} by Sales", height=300)
            st.altair_chart(bar_state, use_container_width=True, theme="streamlit")
        else:
            # إذا لم يجد أي عمود، يطبع أسماء الأعمدة المتاحة لتسهيل التصحيح
            st.warning(f"⚠️ لم يتم العثور على عمود 'State' أو 'Region'. الأعمدة المتاحة في ملفك هي: {', '.join(df.columns)}")

    with col3:
        if 'Ship Mode' in df.columns:
            ship_data = df.groupby('Ship Mode')['Sales'].sum().reset_index()
            bar_ship = alt.Chart(ship_data).mark_bar(color="#9FC131").encode(
                x=alt.X('Sales:Q', axis=alt.Axis(format='~s')),
                y=alt.Y('Ship Mode:N', sort='-x'),
                tooltip=['Ship Mode', alt.Tooltip('Sales:Q', format='$,.2f')]
            ).properties(title="Sales by Ship Mode", height=300)
            st.altair_chart(bar_ship, use_container_width=True, theme="streamlit")
        else:
            st.warning("⚠️ عمود 'Ship Mode' غير موجود في ملف الإكسل.")

# القسم 6: متوسط أيام الشحن واتجاهات الفئات
with dash_6:
    col1, col2 = st.columns([1, 2])

    with col1:
        value = int(np.round(df['days to ship'].mean())) if not df.empty else 0
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': "Average Shipping Days"},
            gauge={'axis': {'range': [df['days to ship'].min() if not df.empty else 0, df['days to ship'].max() if not df.empty else 10]},
                   'bar': {'color': "#005C53"}}
        ))
        fig.update_layout(height=350) 
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    with col2:
        custom_colors = {'Furniture': '#005C53', 'Office Supplies': '#9FC131', 'Technology': '#042940'}
        bars = alt.Chart(df).mark_bar().encode(
            y=alt.Y('sum(Sales):Q', stack='zero', axis=alt.Axis(format='~s')),
            x=alt.X('year:N'),
            color=alt.Color('Category:N', scale=alt.Scale(domain=list(custom_colors.keys()), range=list(custom_colors.values())))
        )
        text = alt.Chart(df).mark_text(dx=-15, dy=30, color='white').encode(
            y=alt.Y('sum(Sales):Q', stack='zero', axis=alt.Axis(format='~s')),
            x=alt.X('year:N'),
            detail='Category:N',
            text=alt.Text('sum(Sales):Q', format='~s')
        )
        chart = (bars + text).properties(title="Sales trends for Product Categories over the years")
        st.altair_chart(chart, use_container_width=True, theme="streamlit")

# القسم 7: الخريطة التفاعلية (Map 🗺️ Sales By Region)
with dash_7:
    st.markdown("### 🗺️ Sales By Region (Map)")
    
    # التحقق من وجود عمود 'State' لرسم الخريطة
    if 'State' in df.columns:
        # تجميع المبيعات حسب الولاية
        state_sales_map = df.groupby('State')['Sales'].sum().reset_index()
        
        # إنشاء الخريطة التفاعلية
        fig_map = px.choropleth(
            state_sales_map,
            locations='State',
            locationmode="USA-states", # لأن بيانات Superstore خاصة بالولايات المتحدة
            color='Sales',
            scope="usa",
            color_continuous_scale="Viridis", # يمكنك تغيير التدرج اللوني (مثل "Blues", "Reds", "Plasma")
            title="Sales Distribution Across US States",
            labels={'Sales': 'Total Sales ($)'}
        )
        
        # تحديث تنسيق الخريطة لتناسب الوضع الداكن
        fig_map.update_layout(
            height=500,
            margin={"r":0,"t":50,"l":0,"b":0},
            coloraxis_colorbar=dict(title="Sales ($)")
        )
        
        st.plotly_chart(fig_map, use_container_width=True, theme="streamlit")
    else:
        st.warning("⚠️ عمود 'State' غير موجود في ملف الإكسل، لا يمكن رسم الخريطة.")
