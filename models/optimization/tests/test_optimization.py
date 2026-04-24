"""Tests for inventory optimization models."""
import pytest
from models.optimization.inventory import InventoryOptimizer, ProductMetrics


def test_reorder_point():
    assert InventoryOptimizer.calculate_reorder_point(5.0, 7) == 35.0


def test_reorder_point_zero():
    assert InventoryOptimizer.calculate_reorder_point(0.0, 7) == 0.0


def test_eoq_basic():
    result = InventoryOptimizer.calculate_eoq(1000, 25, 5)
    assert abs(result - 100.0) < 1.0


def test_eoq_invalid_inputs():
    assert InventoryOptimizer.calculate_eoq(0, 25, 5) == 0.0
    assert InventoryOptimizer.calculate_eoq(1000, 25, 0) == 0.0


def test_days_to_stockout():
    assert InventoryOptimizer.days_to_stockout(100, 10) == 10.0


def test_days_to_stockout_no_demand():
    assert InventoryOptimizer.days_to_stockout(100, 0) is None


def test_identify_slow_movers():
    products = [
        ProductMetrics(1, "A", 100, 10.0, 5.0),
        ProductMetrics(2, "B", 100, 0.1, 5.0),  # slow
        ProductMetrics(3, "C", 100, 5.0, 5.0),
        ProductMetrics(4, "D", 100, 0.05, 5.0),  # slow
    ]
    slow = InventoryOptimizer.identify_slow_movers(products)
    assert isinstance(slow, list)
    assert 2 in slow or 4 in slow  # low demand products are slow movers


def test_identify_slow_movers_empty():
    assert InventoryOptimizer.identify_slow_movers([]) == []


def test_holding_cost():
    cost = InventoryOptimizer.calculate_holding_cost(100, 10.0, 0.25, 1)
    assert abs(cost - 100 * 10 * 0.25 / 12) < 0.01


def test_recommend_order_quantity():
    result = InventoryOptimizer.recommend_order_quantity(
        current_stock=50,
        avg_daily_demand=5.0,
        lead_time_days=7,
        ordering_cost=25.0,
        unit_cost=10.0,
    )
    assert "reorder_point" in result
    assert "economic_order_qty" in result
    assert "should_reorder" in result
    assert result["should_reorder"] == (50 <= result["reorder_point"])
