"""VendorIO Streamlit dashboard entry point."""
import streamlit as st
from pathlib import Path
from dashboard.config import PAGE_TITLE, PAGE_ICON

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
css_path = Path(__file__).parent / "styles" / "theme.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# VendorIO branding at the very top of the sidebar (non-clickable)
st.sidebar.markdown(f"# {PAGE_ICON} {PAGE_TITLE}")
st.sidebar.divider()

pages = [
    st.Page("pages/0_import.py", title="Import Data", icon="📥"),
    st.Page("pages/1_overview.py", title="Overview", icon="📊"),
    st.Page("pages/2_inventory.py", title="Inventory", icon="📦"),
    st.Page("pages/3_costs.py", title="Costs", icon="💰"),
    st.Page("pages/4_forecasts.py", title="Forecasts", icon="🔮"),
    st.Page("pages/5_alerts.py", title="Alerts", icon="🔔"),
]

pg = st.navigation(pages)
pg.run()
