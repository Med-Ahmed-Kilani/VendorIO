"""Streamlit caching wrappers for API calls."""
import streamlit as st
from dashboard.utils import api_client

TTL = 300  # 5-minute cache


@st.cache_data(ttl=TTL)
def cached_kpis(start_date=None, end_date=None):
    return api_client.get_kpis(start_date, end_date)


@st.cache_data(ttl=TTL)
def cached_revenue_trend(days: int = 30):
    return api_client.get_revenue_trend(days)


@st.cache_data(ttl=TTL)
def cached_inventory_status():
    return api_client.get_inventory_status()


@st.cache_data(ttl=TTL)
def cached_profitability():
    return api_client.get_profitability()


@st.cache_data(ttl=TTL)
def cached_cost_summary(start_date=None, end_date=None):
    return api_client.get_cost_summary(start_date, end_date)


@st.cache_data(ttl=TTL)
def cached_recommendations():
    return api_client.get_recommendations(limit=25)


@st.cache_data(ttl=TTL)
def cached_products():
    return api_client.get_products()


@st.cache_data(ttl=TTL)
def cached_revenue_forecast(weeks_ahead: int = 4):
    return api_client.get_revenue_forecast(weeks_ahead)


@st.cache_data(ttl=TTL)
def cached_customer_segments():
    return api_client.get_customer_segments()
