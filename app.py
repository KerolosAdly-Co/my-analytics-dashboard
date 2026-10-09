import streamlit as st
import numpy as np
import pandas as pd
from millify import millify
from streamlit_extras.metric_cards import style_metric_cards
import plotly.graph_objects as go
import altair as alt

st.set_page_config(page_title="Superstore Sales Analytics", page_icon="📈", layout="wide", initial_sidebar_state='collapsed')

st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
        </style>
        """, unsafe_allow_html=True) 

# this function get the % change for any column by year and specified
def get_per_year_change(col, df, metric):
    grp_years = df.groupby('year')[col].agg([metric])[metric]
    grp_years = grp_years.pct_change() * 100
    grp_years.fillna(0, inplace=True)
    grp_years = grp_years.apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else 'NaN')
    return grp_years

# cache the dataset
@st.cache_data(ttl=3600)
def load_data():
    try:
        # قراءة الملف مع تحديد أعمدة التواريخ مباشرة لمنع حدوث أخطاء
        df = pd.read_excel(
            'Sample - Superstore.xls', 
            sheet_name=0,
            parse_dates=['Order Date', 'Ship Date']
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف الإكسل: {e}")
        st.stop()

    # التأكد من تحويل التواريخ إلى نوع datetime في حال فشلت القراءة التلقائية
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')
    
    # إزالة الصفوف التي قد تحتوي على تواريخ فارغة
    df = df.dropna(subset=['Order Date', 'Ship Date'])

    # get the year and store as a new column
    df['year'] = df['Order Date'].dt.year
    # get the difference of Shipped date and order date
    df['days to ship'] = abs((df['Ship Date'] - df['Order Date']).dt.days)

    # get the % change of sales, profit and orders over the years
    grp_years_sales = get_per_year_change('Sales', df, 'sum')
    grp_year_profit = get_per_year_change('Profit', df, 'sum')
    grp_year_orders = get_per_year_change('Order ID', df, 'count')

    return df, grp_years_sales, grp_year_profit, grp_year_orders

# components
sidebar = st.sidebar
dash_1 = st.container()
dash_2 = st.container()
dash_3 = st.container()
dash_4 = st.container()

# load cached data
df_original, grp_years_sales, grp_year_profit, grp_year_orders = load_data()

with sidebar:
    # get the years as a list
    year_list = grp_years_sales.index.to_list()
    year_list.insert(0, "All")
    # create year filter drop down
    selected_year = st.selectbox("Select a year", year_list)

    if selected_year == "All":
        df = df_original
    else:
        df = df_original[df_original['year'] == int(selected_year)]

with dash_1:
    st.markdown("<h2 style='text-align: center;'>Superstore Sales Dashboard</h2>", unsafe_allow_html=True)
    st.write("")

with dash_2:
    # get kpi metrics
    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    total_orders = df['Order ID'].nunique()

    # change the % change of Top KPI's based on filter
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

# plots grp1
with dash_3:
    col1, col2 = st.columns(2)
    top_product_sales = df.groupby('Product Name')['Sales'].sum().nlargest(10).reset_index()
    top_product_profit = df.groupby('Product Name')['Profit'].sum().nlargest(10).reset_index()
    
    with col1:
        chart = alt.Chart(top_product_sales).mark_bar(opacity=0.9, color="#9FC131").encode(
            x='sum(Sales):Q',
            y=alt.Y('Product Name:N', sort='-x')   
        )
        chart = chart.properties(title="Top 10 Selling Products")
        st.altair_chart(chart, use_container_width=True)
        
    with col2:
        chart = alt.Chart(top_product_profit).mark_bar(opacity=0.9, color="#9FC131").encode(
            x='sum(Profit):Q',
            y=alt.Y('Product Name:N', sort='-x')
        )
        chart = chart.properties(title="Top 10 Most Profitable Products")
        st.altair_chart(chart, use_container_width=True)

# dash 4 section
with dash_4:
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
        st.plotly_chart(fig, use_container_width=True)

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
        st.altair_chart(chart, use_container_width=True)
