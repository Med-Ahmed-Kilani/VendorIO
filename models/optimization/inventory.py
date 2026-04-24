"""Inventory optimization: EOQ, ROP, slow-mover detection."""
import math
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class ProductMetrics:
    product_id: int
    name: str
    current_stock: int
    avg_daily_demand: float
    unit_cost: float
    lead_time_days: int = 7


class InventoryOptimizer:
    """Static methods for inventory calculations and classification."""

    @staticmethod
    def calculate_reorder_point(avg_daily_demand: float, lead_time_days: int) -> float:
        """Calculate reorder point for inventory.

        Args:
            avg_daily_demand: Average units sold per day.
            lead_time_days: Days to receive new shipment from supplier.

        Returns:
            Reorder point in units.

        Example:
            >>> InventoryOptimizer.calculate_reorder_point(5.0, 7)
            35.0
        """
        return avg_daily_demand * lead_time_days

    @staticmethod
    def calculate_eoq(
        annual_demand: float, ordering_cost: float, holding_cost_per_unit: float
    ) -> float:
        """Calculate Economic Order Quantity.

        Args:
            annual_demand: Total units demanded per year.
            ordering_cost: Fixed cost per order placed.
            holding_cost_per_unit: Annual holding cost per unit.

        Returns:
            Optimal order quantity in units.

        Example:
            >>> InventoryOptimizer.calculate_eoq(1000, 25, 5)
            100.0
        """
        if holding_cost_per_unit <= 0 or annual_demand <= 0:
            return 0.0
        return math.sqrt(2 * annual_demand * ordering_cost / holding_cost_per_unit)

    @staticmethod
    def days_to_stockout(current_stock: int, avg_daily_demand: float) -> Optional[float]:
        """Days until stock runs out at current sales pace.

        Args:
            current_stock: Current inventory units.
            avg_daily_demand: Average daily units sold.

        Returns:
            Days until stockout, or None if no sales data.
        """
        if avg_daily_demand <= 0:
            return None
        return current_stock / avg_daily_demand

    @staticmethod
    def identify_slow_movers(
        products: list[ProductMetrics], threshold_percentile: float = 25
    ) -> list[int]:
        """Return product IDs in the bottom percentile of inventory turnover.

        Args:
            products: List of ProductMetrics with demand data.
            threshold_percentile: Percentile cutoff (default 25 = bottom quartile).

        Returns:
            List of product IDs classified as slow movers.
        """
        if not products:
            return []
        turnover_rates = []
        for p in products:
            if p.current_stock > 0 and p.avg_daily_demand > 0:
                annual_demand = p.avg_daily_demand * 365
                rate = annual_demand / p.current_stock
            else:
                rate = 0.0
            turnover_rates.append((p.product_id, rate))

        rates_only = [r for _, r in turnover_rates]
        threshold = float(np.percentile(rates_only, threshold_percentile))
        return [pid for pid, rate in turnover_rates if rate <= threshold]

    @staticmethod
    def calculate_holding_cost(
        units: int,
        unit_cost: float,
        holding_rate: float = 0.25,
        period_months: float = 1,
    ) -> float:
        """Monthly holding cost for inventory.

        Args:
            units: Units on hand.
            unit_cost: Cost per unit.
            holding_rate: Annual holding cost as fraction of unit cost.
            period_months: Period in months.

        Returns:
            Holding cost for the period.
        """
        return units * unit_cost * holding_rate * (period_months / 12)

    @staticmethod
    def recommend_order_quantity(
        current_stock: int,
        avg_daily_demand: float,
        lead_time_days: int,
        ordering_cost: float,
        unit_cost: float,
        holding_rate: float = 0.25,
    ) -> dict:
        """Full reorder recommendation combining ROP and EOQ.

        Returns:
            Dict with reorder_point, eoq, should_reorder, days_to_stockout.
        """
        annual_demand = avg_daily_demand * 365
        rop = InventoryOptimizer.calculate_reorder_point(avg_daily_demand, lead_time_days)
        holding_per_unit = unit_cost * holding_rate
        eoq = InventoryOptimizer.calculate_eoq(annual_demand, ordering_cost, holding_per_unit)
        dts = InventoryOptimizer.days_to_stockout(current_stock, avg_daily_demand)
        return {
            "reorder_point": round(rop, 1),
            "economic_order_qty": round(eoq, 0),
            "should_reorder": current_stock <= rop,
            "days_to_stockout": round(dts, 1) if dts is not None else None,
        }
