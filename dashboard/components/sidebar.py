"""Sidebar filters and navigation."""
from datetime import date, timedelta
import streamlit as st


def render_date_filters() -> tuple[date, date]:
    """Render date range picker in sidebar, return (start_date, end_date)."""
    st.sidebar.subheader("📅 Date Range")
    preset = st.sidebar.selectbox(
        "Quick select", ["Last 30 days", "Last 90 days", "Last 365 days", "Custom"]
    )
    today = date.today()
    if preset == "Last 30 days":
        start, end = today - timedelta(days=30), today
    elif preset == "Last 90 days":
        start, end = today - timedelta(days=90), today
    elif preset == "Last 365 days":
        start, end = today - timedelta(days=365), today
    else:
        start = st.sidebar.date_input("Start date", value=today - timedelta(days=30))
        end = st.sidebar.date_input("End date", value=today)
    return start, end


def render_category_filter(categories: list[str]) -> list[str]:
    """Multi-select category filter."""
    st.sidebar.subheader("🏷️ Category Filter")
    return st.sidebar.multiselect("Categories", options=categories, default=categories)


def render_sidebar_info() -> None:
    """Bottom sidebar: app info and refresh button."""
    st.sidebar.divider()
    st.sidebar.caption("VendorIO v1.0")
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
