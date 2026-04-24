"""Tests for analytics models: segmentation and profitability."""
import pytest
from datetime import date
from models.analytics.segmentation import CustomerRecord, rfm_score, segment_summary
from models.analytics.profitability import ProductSalesData, analyse_profitability, identify_low_margin_products


def _make_customers():
    return [
        CustomerRecord(1, date(2024, 3, 1), 10, 500.0),
        CustomerRecord(2, date(2024, 1, 1), 1, 50.0),
        CustomerRecord(3, date(2024, 4, 1), 5, 250.0),
        CustomerRecord(4, date(2023, 6, 1), 2, 100.0),
        CustomerRecord(5, date(2024, 4, 15), 20, 1000.0),
    ]


def test_rfm_score_basic():
    customers = _make_customers()
    df = rfm_score(customers, reference_date=date(2024, 5, 1))
    assert len(df) == len(customers)
    assert "segment" in df.columns
    assert "rfm_score" in df.columns


def test_rfm_score_empty():
    df = rfm_score([])
    assert df.empty


def test_segment_summary():
    customers = _make_customers()
    df = rfm_score(customers)
    summary = segment_summary(df)
    assert isinstance(summary, list)
    assert len(summary) > 0
    for seg in summary:
        assert "segment" in seg
        assert "customer_count" in seg


def _make_products():
    return [
        ProductSalesData(1, "Coffee", "Beverages", 15.99, 5.00, 100, 50),
        ProductSalesData(2, "Tea", "Beverages", 8.99, 8.50, 20, 10),  # low margin
        ProductSalesData(3, "Sugar", "Food", 3.99, 1.00, 200, 100),
    ]


def test_analyse_profitability():
    products = _make_products()
    df = analyse_profitability(products)
    assert len(df) == len(products)
    assert "gross_profit" in df.columns
    assert "margin_pct" in df.columns
    # Should be sorted by gross_profit descending
    assert df["gross_profit"].iloc[0] >= df["gross_profit"].iloc[-1]


def test_identify_low_margin_products():
    products = _make_products()
    df = analyse_profitability(products)
    low = identify_low_margin_products(df, threshold_pct=10.0)
    # Tea has margin ~(8.99-8.50)/8.99*100 ≈ 5.5% — should be flagged
    assert len(low) >= 1
    assert (low["margin_pct"] < 10.0).all()
