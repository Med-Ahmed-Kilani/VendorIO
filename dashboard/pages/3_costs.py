"""Page 3: Cost Analysis — margins, COGS, holding costs, savings forecast."""
import streamlit as st
from dashboard.components.charts import margin_chart, cost_breakdown_chart
from dashboard.components.tables import profitability_table
from dashboard.components.sidebar import render_date_filters, render_sidebar_info
from dashboard.utils.cache import cached_cost_summary, cached_profitability
from dashboard.utils.formatters import fmt_currency, fmt_pct

start_date, end_date = render_date_filters()
render_sidebar_info()

st.title("💸 Cost Analysis")

summary = cached_cost_summary(start_date, end_date)
profitability = cached_profitability()

if summary:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Revenue", fmt_currency(summary.get("total_revenue")))
    c2.metric("📦 COGS", fmt_currency(summary.get("total_cogs")))
    c3.metric("📈 Gross Profit", fmt_currency(summary.get("gross_profit")))
    c4.metric("📊 Gross Margin", fmt_pct(summary.get("gross_margin_pct")))

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("💡 Savings Opportunity")
        savings = summary.get("potential_savings", 0)
        holding_monthly = summary.get("total_holding_cost_monthly", 0)
        st.info(
            f"Current monthly holding cost: **{fmt_currency(holding_monthly)}**  \n"
            f"Estimated monthly savings if top recommendations are implemented: **{fmt_currency(savings)}**"
        )
    with col2:
        if holding_monthly > 0:
            import plotly.graph_objects as go
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=summary.get("gross_margin_pct", 0),
                title={"text": "Gross Margin %"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "steps": [
                        {"range": [0, 20], "color": "#FEE2E2"},
                        {"range": [20, 40], "color": "#FEF3C7"},
                        {"range": [40, 100], "color": "#DCFCE7"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 4}, "value": 10},
                },
            ))
            fig.update_layout(height=200)
            st.plotly_chart(fig, use_container_width=True)

st.divider()

if profitability:
    # Warnings for low-margin products
    low_margin = [p for p in profitability if p.get("margin_pct") is not None and p["margin_pct"] < 10]
    if low_margin:
        with st.expander(f"⚠️ {len(low_margin)} products with margin < 10%", expanded=True):
            for p in low_margin:
                st.warning(f"**{p['product_name']}** — margin: {p['margin_pct']:.1f}%")

    tab1, tab2 = st.tabs(["📊 Margin Chart", "📋 Full Table"])
    with tab1:
        margin_chart(profitability)
        cost_breakdown_chart(profitability)
    with tab2:
        profitability_table(profitability)

    # CSV export
    import pandas as pd
    csv = pd.DataFrame(profitability).to_csv(index=False)
    st.download_button("⬇️ Download Profitability Report (CSV)", csv, "profitability.csv", "text/csv")
