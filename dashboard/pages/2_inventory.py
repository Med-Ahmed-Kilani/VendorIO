"""Page 2: Inventory Optimization — stock levels, reorder alerts, holding costs."""
import streamlit as st
import pandas as pd
from pathlib import Path
from dashboard.config import PAGE_TITLE, PAGE_ICON
from dashboard.components.charts import inventory_heatmap, holding_cost_chart
from dashboard.components.tables import inventory_table
from dashboard.components.sidebar import render_sidebar_info
from dashboard.utils.cache import cached_inventory_status
from dashboard.utils.formatters import fmt_currency, fmt_number

st.set_page_config(page_title=f"Inventory — {PAGE_TITLE}", page_icon=PAGE_ICON, layout="wide")

css_path = Path(__file__).parent.parent / "styles" / "theme.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.sidebar.title(f"{PAGE_ICON} {PAGE_TITLE}")
render_sidebar_info()

st.title("📦 Inventory Optimization")

inventory = cached_inventory_status()

if not inventory:
    st.warning("No inventory data. Load sample data with: `python scripts/load_sample_data.py`")
    st.stop()

df = pd.DataFrame(inventory)
critical = df[df["status"] == "critical"]
warning = df[df["status"] == "warning"]
needs_reorder = df[df["needs_reorder"] == True]

# Summary KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("🔴 Critical (< 7d)", len(critical))
c2.metric("🟡 Warning (< 14d)", len(warning))
c3.metric("⚠️ Needs Reorder", len(needs_reorder))
total_holding = df["holding_cost_monthly"].sum()
c4.metric("💰 Total Holding/mo", fmt_currency(total_holding))

st.divider()

# Filters
col_filter, col_status = st.columns([2, 1])
with col_filter:
    search = st.text_input("🔍 Search products", "")
with col_status:
    status_filter = st.selectbox("Status", ["All", "critical", "warning", "ok"])

filtered = df.copy()
if search:
    filtered = filtered[filtered["product_name"].str.contains(search, case=False, na=False)]
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]

st.subheader(f"Inventory Status ({len(filtered)} products)")
inventory_table(filtered.to_dict(orient="records"))

# Download reorder list
reorder_df = filtered[filtered["needs_reorder"] == True][["product_name", "category", "current_stock", "reorder_point", "days_to_stockout"]]
if not reorder_df.empty:
    csv = reorder_df.to_csv(index=False)
    st.download_button("⬇️ Download Reorder List (CSV)", csv, "reorder_list.csv", "text/csv")

st.divider()

col1, col2 = st.columns(2)
with col1:
    inventory_heatmap(inventory)
with col2:
    holding_cost_chart(inventory)
