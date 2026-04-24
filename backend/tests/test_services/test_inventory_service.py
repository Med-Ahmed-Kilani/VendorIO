"""Tests for inventory service calculations."""
import pytest
from backend.services.inventory_service import (
    calculate_reorder_point,
    calculate_eoq,
    days_to_stockout,
    classify_turnover,
    get_inventory_status,
    get_product_health,
)


def test_calculate_reorder_point():
    result = calculate_reorder_point(avg_daily_demand=10.0, lead_time_days=7)
    assert result == 70.0


def test_calculate_reorder_point_zero_demand():
    assert calculate_reorder_point(0.0, 7) == 0.0


def test_calculate_eoq_basic():
    result = calculate_eoq(annual_demand=1000, ordering_cost=25, holding_cost_per_unit=5)
    assert abs(result - 100.0) < 1.0  # √(2*1000*25/5) = √10000 = 100


def test_calculate_eoq_zero_demand():
    assert calculate_eoq(0, 25, 5) == 0.0


def test_calculate_eoq_zero_holding():
    assert calculate_eoq(1000, 25, 0) == 0.0


def test_days_to_stockout_normal():
    result = days_to_stockout(current_stock=100, avg_daily_demand=10)
    assert result == 10.0


def test_days_to_stockout_zero_demand():
    assert days_to_stockout(100, 0) is None


def test_classify_turnover_slow():
    rates = [1, 2, 3, 4, 5, 6, 7, 8]
    assert classify_turnover(1, rates) == "slow"


def test_classify_turnover_fast():
    rates = [1, 2, 3, 4, 5, 6, 7, 8]
    assert classify_turnover(8, rates) == "fast"


def test_classify_turnover_average():
    rates = [1, 2, 3, 4, 5, 6, 7, 8]
    assert classify_turnover(4, rates) == "average"


def test_get_inventory_status(db, sample_products):
    result = get_inventory_status(db)
    assert isinstance(result, list)
    assert len(result) == len(sample_products)
    for item in result:
        assert "status" in item.__dict__ or hasattr(item, "status")


def test_get_product_health(db, sample_product):
    result = get_product_health(db, sample_product.id)
    assert result is not None
    assert result.product_id == sample_product.id
    assert result.current_stock == sample_product.current_stock


def test_get_product_health_not_found(db):
    result = get_product_health(db, 99999)
    assert result is None
