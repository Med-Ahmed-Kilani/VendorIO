"""Tests for metrics service."""
from datetime import datetime, timedelta
import pytest
from backend.services.metrics_service import get_kpi_metrics, get_revenue_trend, get_customer_segments


def test_get_kpi_metrics_empty(db):
    result = get_kpi_metrics(db)
    assert "total_revenue" in result
    assert "order_count" in result
    assert result["total_revenue"] == 0.0
    assert result["order_count"] == 0


def test_get_kpi_metrics_date_range(db):
    start = datetime.utcnow() - timedelta(days=30)
    end = datetime.utcnow()
    result = get_kpi_metrics(db, start_date=start, end_date=end)
    assert result["period_start"] is not None
    assert result["period_end"] is not None


def test_kpi_structure(db):
    result = get_kpi_metrics(db)
    expected_keys = [
        "total_revenue", "total_profit", "order_count",
        "avg_order_value", "repeat_customer_rate", "top_products", "bottom_products"
    ]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"


def test_get_revenue_trend(db):
    start = datetime.utcnow() - timedelta(days=30)
    end = datetime.utcnow()
    result = get_revenue_trend(db, start, end)
    assert isinstance(result, list)


def test_get_customer_segments_empty(db):
    result = get_customer_segments(db)
    assert isinstance(result, list)
