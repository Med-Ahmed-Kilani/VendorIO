"""Page 1: Business Overview — KPIs, revenue trend, top products."""
import streamlit as st
from dashboard.components.kpi_cards import kpi_row, kpi_secondary
from dashboard.components.charts import revenue_trend_chart, top_products_chart
from dashboard.components.sidebar import render_date_filters, render_sidebar_info
from dashboard.utils.cache import cached_kpis, cached_revenue_trend, cached_customer_segments
from dashboard.utils.formatters import fmt_currency

# --- Sidebar ---
start_date, end_date = render_date_filters()
render_sidebar_info()

# --- Main content ---
st.title("📊 Business Overview")
st.caption(f"Period: {start_date} → {end_date}")

kpis = cached_kpis(start_date, end_date)
kpi_row(kpis)
kpi_secondary(kpis)

st.divider()

col1, col2 = st.columns(2)
with col1:
    trend = cached_revenue_trend(days=(end_date - start_date).days or 30)
    revenue_trend_chart(trend)

with col2:
    if kpis and kpis.get("top_products"):
        top_products_chart(kpis["top_products"], title="Top 5 Products by Revenue")
    else:
        st.info("No product data available")

st.divider()

# Customer segments summary
st.subheader("👥 Customer Segments")
segments = cached_customer_segments()
if segments:
    import pandas as pd
    df = pd.DataFrame(segments)
    seg_summary = df.groupby("segment").agg(
        count=("customer_id", "count"),
        avg_spent=("total_spent", "mean"),
        avg_orders=("order_count", "mean"),
    ).reset_index()
    seg_summary.columns = ["Segment", "Customers", "Avg Lifetime Value", "Avg Orders"]
    seg_summary["Avg Lifetime Value"] = seg_summary["Avg Lifetime Value"].apply(fmt_currency)
    st.dataframe(seg_summary, use_container_width=True, hide_index=True)
else:
    st.info("No customer data available")

# Bottom products (lowest revenue)
if kpis and kpis.get("bottom_products"):
    with st.expander("⚠️ Bottom 5 Products by Revenue"):
        top_products_chart(kpis["bottom_products"], title="Bottom 5 Products")
