"""Tests for cost service."""
import pytest
from backend.services.cost_service import get_product_profitability, get_cost_summary


def test_get_product_profitability_empty(db):
    result = get_product_profitability(db)
    assert isinstance(result, list)


def test_get_product_profitability_with_products(db, sample_products):
    result = get_product_profitability(db)
    assert len(result) >= len(sample_products)
    for item in result:
        assert "product_id" in item
        assert "gross_profit" in item
        assert "margin_pct" in item


def test_profitability_sorted_by_profit(db, sample_products):
    result = get_product_profitability(db)
    profits = [r["gross_profit"] for r in result]
    assert profits == sorted(profits, reverse=True)


def test_get_cost_summary_empty(db):
    result = get_cost_summary(db)
    assert "total_revenue" in result
    assert "total_cogs" in result
    assert "gross_profit" in result


def test_get_cost_summary_with_data(db, sample_products):
    result = get_cost_summary(db)
    assert result["total_holding_cost_monthly"] >= 0
    assert result["potential_savings"] >= 0
