"""Reusable Plotly chart components."""
from typing import Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from dashboard.config import COLORS


def revenue_trend_chart(trend_data: list[dict]) -> None:
    """Line chart of daily revenue over time."""
    if not trend_data:
        st.info("No revenue data to display")
        return
    df = pd.DataFrame(trend_data)
    fig = px.line(
        df, x="date", y="revenue",
        title="Daily Revenue Trend",
        labels={"date": "Date", "revenue": "Revenue ($)"},
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.update_layout(hovermode="x unified", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def top_products_chart(products: list[dict], title: str = "Top Products by Revenue") -> None:
    """Horizontal bar chart of top products."""
    if not products:
        st.info("No product data available")
        return
    df = pd.DataFrame(products)
    df = df.sort_values("revenue")
    fig = px.bar(
        df, x="revenue", y="product_name",
        orientation="h",
        title=title,
        labels={"revenue": "Revenue ($)", "product_name": "Product"},
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def inventory_heatmap(inventory: list[dict]) -> None:
    """Scatter/heatmap of inventory health: stock vs days-to-stockout."""
    if not inventory:
        st.info("No inventory data")
        return
    df = pd.DataFrame(inventory)
    df = df.dropna(subset=["days_to_stockout"])
    color_map = {"ok": COLORS["success"], "warning": COLORS["warning"], "critical": COLORS["danger"]}
    df["color"] = df["status"].map(color_map)
    fig = px.scatter(
        df, x="turnover_rate", y="days_to_stockout",
        color="status",
        color_discrete_map={"ok": COLORS["success"], "warning": COLORS["warning"], "critical": COLORS["danger"]},
        hover_name="product_name",
        hover_data={"current_stock": True, "holding_cost_monthly": True},
        title="Inventory Health: Turnover vs Days to Stockout",
        labels={"turnover_rate": "Annual Turnover Rate", "days_to_stockout": "Days to Stockout"},
    )
    fig.add_hline(y=7, line_dash="dash", line_color=COLORS["danger"], annotation_text="Critical (7d)")
    fig.add_hline(y=14, line_dash="dash", line_color=COLORS["warning"], annotation_text="Warning (14d)")
    st.plotly_chart(fig, use_container_width=True)


def holding_cost_chart(inventory: list[dict]) -> None:
    """Bar chart of monthly holding costs by product."""
    if not inventory:
        return
    df = pd.DataFrame(inventory)
    df = df[df["holding_cost_monthly"] > 0].sort_values("holding_cost_monthly", ascending=False).head(15)
    fig = px.bar(
        df, x="product_name", y="holding_cost_monthly",
        title="Monthly Holding Cost by Product (Top 15)",
        labels={"product_name": "Product", "holding_cost_monthly": "Monthly Cost ($)"},
        color="status",
        color_discrete_map={"ok": COLORS["success"], "warning": COLORS["warning"], "critical": COLORS["danger"]},
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)


def margin_chart(profitability: list[dict]) -> None:
    """Scatter of margin % vs revenue for all products."""
    if not profitability:
        return
    df = pd.DataFrame(profitability)
    df = df.dropna(subset=["margin_pct"])
    fig = px.scatter(
        df, x="total_revenue", y="margin_pct",
        hover_name="product_name",
        color="margin_pct",
        color_continuous_scale="RdYlGn",
        size="total_units_sold",
        title="Product Margin vs Revenue",
        labels={"total_revenue": "Total Revenue ($)", "margin_pct": "Gross Margin (%)"},
    )
    fig.add_hline(y=10, line_dash="dash", line_color=COLORS["warning"], annotation_text="10% minimum")
    st.plotly_chart(fig, use_container_width=True)


def forecast_chart(forecast_data: dict, title: str = "Revenue Forecast") -> None:
    """Line chart with confidence band for forecast data."""
    if not forecast_data or "forecast" not in forecast_data:
        st.info("Forecast unavailable — need at least 14 days of order history")
        return
    rows = forecast_data["forecast"]
    df = pd.DataFrame(rows)
    if df.empty:
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["forecast"],
        name="Forecast",
        line=dict(color=COLORS["primary"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([df["date"], df["date"][::-1]]),
        y=pd.concat([df["ci_upper"], df["ci_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(37,99,235,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="80% Confidence",
    ))
    mape = forecast_data.get("mape")
    mape_str = f"  |  MAPE: {mape:.1%}" if mape is not None else ""
    fig.update_layout(
        title=f"{title}{mape_str}",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def cost_breakdown_chart(profitability: list[dict]) -> None:
    """Stacked bar: COGS + Holding cost vs Revenue for top products."""
    if not profitability:
        return
    df = pd.DataFrame(profitability).head(12)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="COGS", x=df["product_name"], y=df["total_cogs"]))
    fig.add_trace(go.Bar(name="Holding Cost", x=df["product_name"], y=df["holding_cost_annual"] / 12))
    fig.add_trace(go.Scatter(
        name="Revenue", x=df["product_name"], y=df["total_revenue"],
        mode="markers", marker=dict(color=COLORS["primary"], size=10),
    ))
    fig.update_layout(
        barmode="stack",
        title="Cost Breakdown vs Revenue (Top 12 Products)",
        xaxis_tickangle=45,
    )
    st.plotly_chart(fig, use_container_width=True)
