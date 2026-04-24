"""Reusable KPI metric card components."""
import streamlit as st
from dashboard.utils.formatters import fmt_currency, fmt_pct, fmt_number


def kpi_row(kpis: dict) -> None:
    """Render a row of 4 KPI metric cards from /metrics/kpi response."""
    if not kpis:
        st.warning("No KPI data available")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Revenue", fmt_currency(kpis.get("total_revenue")))
    c2.metric("📈 Profit", fmt_currency(kpis.get("total_profit")))
    c3.metric("🛒 Orders", fmt_number(kpis.get("order_count")))
    c4.metric("🔄 Repeat Rate", fmt_pct(kpis.get("repeat_customer_rate", 0) * 100))


def kpi_secondary(kpis: dict) -> None:
    """Render secondary KPI metrics."""
    if not kpis:
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("💳 Avg Order Value", fmt_currency(kpis.get("avg_order_value")))
    c2.metric("👥 Unique Customers", fmt_number(kpis.get("total_customers")))
