"""Product profitability analysis."""
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class ProductSalesData:
    product_id: int
    name: str
    category: Optional[str]
    unit_price: float
    cost_per_unit: Optional[float]
    total_units_sold: int
    current_stock: int
    holding_cost_rate: float = 0.25


def analyse_profitability(products: list[ProductSalesData]) -> pd.DataFrame:
    """Compute profitability metrics for each product.

    Args:
        products: List of ProductSalesData.

    Returns:
        DataFrame ranked by gross profit descending.
    """
    rows = []
    for p in products:
        revenue = p.unit_price * p.total_units_sold
        cogs = (p.cost_per_unit or 0) * p.total_units_sold
        holding_annual = (p.cost_per_unit or p.unit_price) * p.current_stock * p.holding_cost_rate
        gross_profit = revenue - cogs
        margin = (gross_profit / revenue) if revenue > 0 else None
        rows.append({
            "product_id": p.product_id,
            "name": p.name,
            "category": p.category,
            "revenue": round(revenue, 2),
            "cogs": round(cogs, 2),
            "holding_cost_annual": round(holding_annual, 2),
            "gross_profit": round(gross_profit, 2),
            "margin_pct": round(margin * 100, 1) if margin is not None else None,
            "total_units_sold": p.total_units_sold,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("gross_profit", ascending=False).reset_index(drop=True)
    return df


def identify_low_margin_products(df: pd.DataFrame, threshold_pct: float = 10.0) -> pd.DataFrame:
    """Flag products with margin below threshold.

    Args:
        df: Output of analyse_profitability().
        threshold_pct: Margin percentage below which a product is flagged.

    Returns:
        Filtered DataFrame of low-margin products.
    """
    if df.empty:
        return df
    return df[df["margin_pct"] < threshold_pct].copy()
