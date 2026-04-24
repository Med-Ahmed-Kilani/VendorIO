"""Reusable table components."""
from typing import Optional
import pandas as pd
import streamlit as st
from dashboard.config import STATUS_COLORS
from dashboard.utils.formatters import fmt_currency, fmt_days, fmt_pct, fmt_number


def inventory_table(inventory: list[dict]) -> None:
    """Sortable inventory status table with colour-coded status."""
    if not inventory:
        st.info("No inventory data")
        return
    df = pd.DataFrame(inventory)
    display = df[[
        "product_name", "category", "current_stock", "reorder_point",
        "days_to_stockout", "turnover_rate", "holding_cost_monthly", "status", "needs_reorder"
    ]].copy()
    display.columns = [
        "Product", "Category", "Stock", "Reorder Point",
        "Days to Stockout", "Turnover/yr", "Holding $/mo", "Status", "Needs Reorder"
    ]
    display["Days to Stockout"] = display["Days to Stockout"].apply(lambda x: fmt_days(x))
    display["Holding $/mo"] = display["Holding $/mo"].apply(lambda x: fmt_currency(x))
    display["Needs Reorder"] = display["Needs Reorder"].apply(lambda x: "⚠️ Yes" if x else "")

    def highlight_status(row):
        color_map = {"critical": "background-color: #FEE2E2", "warning": "background-color: #FEF3C7", "ok": ""}
        color = color_map.get(row["Status"], "")
        return [color] * len(row)

    st.dataframe(
        display.style.apply(highlight_status, axis=1),
        use_container_width=True,
        hide_index=True,
    )


def profitability_table(profitability: list[dict]) -> None:
    """Margin analysis table ranked by gross profit."""
    if not profitability:
        st.info("No profitability data")
        return
    df = pd.DataFrame(profitability)
    display = df[[
        "product_name", "category", "total_revenue", "total_cogs",
        "gross_profit", "margin_pct", "total_units_sold"
    ]].copy()
    display.columns = ["Product", "Category", "Revenue", "COGS", "Gross Profit", "Margin %", "Units Sold"]
    for col in ["Revenue", "COGS", "Gross Profit"]:
        display[col] = display[col].apply(lambda x: fmt_currency(x))
    display["Margin %"] = display["Margin %"].apply(lambda x: fmt_pct(x) if x else "N/A")

    def highlight_margin(row):
        try:
            val = float(str(row["Margin %"]).replace("%", "").replace("N/A", "50"))
            if val < 10:
                return ["background-color: #FEE2E2"] * len(row)
            if val < 20:
                return ["background-color: #FEF3C7"] * len(row)
        except (ValueError, TypeError):
            pass
        return [""] * len(row)

    st.dataframe(
        display.style.apply(highlight_margin, axis=1),
        use_container_width=True,
        hide_index=True,
    )


def recommendations_table(recs: list[dict]) -> None:
    """Priority table of recommendations."""
    if not recs:
        st.success("No urgent recommendations — business looks healthy!")
        return
    from dashboard.config import URGENCY_EMOJI
    for r in recs:
        emoji = URGENCY_EMOJI.get(r.get("urgency", "low"), "")
        urgency = r.get("urgency", "").upper()
        with st.container():
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{emoji} [{urgency}]** — {r.get('product_name', '')} ({r.get('type', '')})")
            col1.markdown(f"📌 **Action:** {r.get('action', '')}")
            col1.markdown(f"💡 **Impact:** {r.get('impact', '')}")
            col2.markdown(f"Days left: **{r.get('days_remaining', 'N/A')}**" if "days_remaining" in r else "")
            st.divider()
