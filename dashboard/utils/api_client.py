"""HTTP client for the FastAPI backend."""
from typing import Any, Optional
import httpx
import streamlit as st
from dashboard.config import API_BASE_URL


def _get(endpoint: str, params: Optional[dict] = None) -> Any:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = httpx.get(url, params=params, timeout=15.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
        return None
    except httpx.RequestError as e:
        st.error(f"Cannot connect to backend at {API_BASE_URL}. Is the server running?")
        return None


def _post_file(endpoint: str, file_bytes: bytes, filename: str) -> Any:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = httpx.post(
            url,
            files={"file": (filename, file_bytes, "text/csv")},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
        return None
    except httpx.RequestError:
        st.error(f"Cannot connect to backend at {API_BASE_URL}")
        return None


def _post(endpoint: str, payload: dict) -> Any:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = httpx.post(url, json=payload, timeout=15.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
        return None
    except httpx.RequestError:
        st.error(f"Cannot connect to backend at {API_BASE_URL}")
        return None


# --- Public API helpers ---

def get_health() -> Optional[dict]:
    return httpx.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5.0).json()


def get_kpis(start_date=None, end_date=None) -> Optional[dict]:
    params = {}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    return _get("/metrics/kpi", params=params)


def get_revenue_trend(days: int = 30) -> Optional[list]:
    return _get("/metrics/revenue-trend", params={"days": days})


def get_inventory_status() -> Optional[list]:
    return _get("/inventory/status")


def get_product_health(product_id: int) -> Optional[dict]:
    return _get(f"/inventory/{product_id}/health")


def get_cost_summary(start_date=None, end_date=None) -> Optional[dict]:
    params = {}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    return _get("/metrics/cost-summary", params=params)


def get_profitability() -> Optional[list]:
    return _get("/metrics/profitability")


def get_revenue_forecast(weeks_ahead: int = 4) -> Optional[dict]:
    return _get("/forecasts/revenue", params={"weeks_ahead": weeks_ahead})


def get_demand_forecast(product_id: int, weeks_ahead: int = 4) -> Optional[dict]:
    return _get("/forecasts/demand", params={"product_id": product_id, "weeks_ahead": weeks_ahead})


def get_recommendations(limit: int = 20) -> Optional[dict]:
    return _get("/recommendations", params={"limit": limit})


def get_products() -> Optional[dict]:
    return _get("/products")


def get_customer_segments() -> Optional[list]:
    return _get("/metrics/customer-segments")


def import_inventory_csv(file_bytes: bytes, filename: str) -> Optional[dict]:
    return _post_file("/import/inventory", file_bytes, filename)


def import_products_csv(file_bytes: bytes, filename: str) -> Optional[dict]:
    return _post_file("/import/products", file_bytes, filename)


def import_orders_csv(file_bytes: bytes, filename: str) -> Optional[dict]:
    return _post_file("/import/orders", file_bytes, filename)


def clear_all_data() -> Optional[dict]:
    url = f"{API_BASE_URL}/import/clear"
    try:
        resp = httpx.post(url, params={"confirm": True}, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
        return None
    except httpx.RequestError:
        st.error(f"Cannot connect to backend at {API_BASE_URL}")
        return None
