"""Page 4: Demand Forecasts — revenue + product-level forecasts."""
import streamlit as st
from pathlib import Path
from dashboard.config import PAGE_TITLE, PAGE_ICON
from dashboard.components.charts import forecast_chart
from dashboard.components.sidebar import render_sidebar_info
from dashboard.utils.cache import cached_revenue_forecast, cached_products
from dashboard.utils import api_client

st.set_page_config(page_title=f"Forecasts — {PAGE_TITLE}", page_icon=PAGE_ICON, layout="wide")

css_path = Path(__file__).parent.parent / "styles" / "theme.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.sidebar.title(f"{PAGE_ICON} {PAGE_TITLE}")
weeks_ahead = st.sidebar.slider("Weeks to forecast", 1, 12, 4)
render_sidebar_info()

st.title("🔮 Demand Forecasts")

tab1, tab2 = st.tabs(["📈 Revenue Forecast", "📦 Product Forecast"])

with tab1:
    st.subheader("4-Week Revenue Forecast")
    fc = cached_revenue_forecast(weeks_ahead)
    if fc:
        mape = fc.get("mape")
        model = fc.get("model", "ARIMA")
        c1, c2, c3 = st.columns(3)
        c1.metric("Model", model)
        c2.metric("MAPE", f"{mape:.1%}" if mape is not None else "N/A")
        c3.metric("Weeks Ahead", weeks_ahead)
        forecast_chart(fc, title=f"Revenue Forecast — Next {weeks_ahead} Weeks")

        # Weekly summary table
        if "forecast" in fc:
            import pandas as pd
            df = pd.DataFrame(fc["forecast"])
            # Group into weeks
            if not df.empty:
                df["week_num"] = (pd.to_datetime(df["date"]).dt.to_period("W"))
                weekly = df.groupby("week_num").agg(
                    revenue=("forecast", "sum"),
                    ci_lower=("ci_lower", "sum"),
                    ci_upper=("ci_upper", "sum"),
                ).reset_index()
                weekly["week_num"] = weekly["week_num"].astype(str)
                weekly.columns = ["Week", "Forecast Revenue", "Lower Bound", "Upper Bound"]
                for col in ["Forecast Revenue", "Lower Bound", "Upper Bound"]:
                    weekly[col] = weekly[col].apply(lambda x: f"${x:,.0f}")
                st.dataframe(weekly, use_container_width=True, hide_index=True)
    else:
        st.info("📊 Forecast unavailable. Load at least 2 weeks of order history to enable forecasting.")

with tab2:
    st.subheader("Product-Level Demand Forecast")
    products_resp = cached_products()
    if products_resp and products_resp.get("data"):
        products = products_resp["data"]
        product_map = {p["name"]: p["id"] for p in products}
        selected_name = st.selectbox("Select product", list(product_map.keys()))
        if selected_name:
            product_id = product_map[selected_name]
            with st.spinner("Generating forecast..."):
                pfc = api_client.get_demand_forecast(product_id, weeks_ahead)
            if pfc:
                mape = pfc.get("mape")
                c1, c2 = st.columns(2)
                c1.metric("Model", pfc.get("model", "ARIMA"))
                c2.metric("MAPE", f"{mape:.1%}" if mape is not None else "N/A")
                forecast_chart(pfc, title=f"Demand Forecast: {selected_name}")
            else:
                st.info(f"Insufficient data to forecast '{selected_name}'. Need at least 14 order days.")
    else:
        st.info("No products found. Load sample data first.")

st.divider()
st.caption("ℹ️ Forecast model: ARIMA with auto-order selection. Confidence band = 80% CI.")
