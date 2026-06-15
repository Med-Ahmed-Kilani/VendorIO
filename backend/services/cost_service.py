from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.final_product import FinalProduct
from backend.models.recipe import Recipe
from backend.models.raw_material import RawMaterial, RawMaterialInventory
from backend.models.order import Order, OrderItem
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

HOLDING_COST_RATE = settings.holding_cost_rate


def get_product_profitability(db: Session) -> list[dict]:
    """Margin per product using recipe unit_cost (default/NULL-size recipe)."""
    rows = (
        db.query(
            FinalProduct.id,
            FinalProduct.name,
            FinalProduct.category,
            FinalProduct.unit_price,
            Recipe.unit_cost,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_sold"),
        )
        .outerjoin(Recipe, (Recipe.product_id == FinalProduct.id) & (Recipe.size.is_(None)))
        .outerjoin(OrderItem, OrderItem.product_id == FinalProduct.id)
        .group_by(FinalProduct.id, FinalProduct.name, FinalProduct.category,
                  FinalProduct.unit_price, Recipe.unit_cost)
        .all()
    )

    result = []
    for row in rows:
        total_sold = int(row.total_sold or 0)
        unit_price = float(row.unit_price)
        unit_cost = float(row.unit_cost or 0)
        revenue = total_sold * unit_price
        cogs = total_sold * unit_cost
        gross_profit = revenue - cogs
        margin = (gross_profit / revenue) if revenue > 0 else None

        result.append({
            "product_id": row.id,
            "product_name": row.name,
            "category": row.category,
            "unit_price": unit_price,
            "cost_per_unit": unit_cost,
            "total_units_sold": total_sold,
            "total_revenue": round(revenue, 2),
            "total_cogs": round(cogs, 2),
            "holding_cost_annual": 0.0,  # holding is now per-material (see get_cost_summary)
            "gross_profit": round(gross_profit, 2),
            "margin_pct": round(margin * 100, 1) if margin is not None else None,
        })
    return sorted(result, key=lambda x: x["gross_profit"], reverse=True)


def get_cost_summary(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Aggregate revenue, COGS (from snapshotted unit_cost), and material holding costs."""
    rev_q = db.query(func.sum(Order.total_amount)).filter(Order.status == "completed")
    if start_date:
        rev_q = rev_q.filter(Order.order_date >= start_date)
    if end_date:
        rev_q = rev_q.filter(Order.order_date <= end_date)
    total_revenue = float(rev_q.scalar() or 0)

    # COGS from snapshotted unit_cost on each order item
    cogs_q = (
        db.query(func.sum(OrderItem.unit_cost * OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.status == "completed", OrderItem.unit_cost.isnot(None))
    )
    if start_date:
        cogs_q = cogs_q.filter(Order.order_date >= start_date)
    if end_date:
        cogs_q = cogs_q.filter(Order.order_date <= end_date)
    total_cogs = float(cogs_q.scalar() or 0)

    # Holding cost: granular per raw material
    total_holding = float(
        db.query(
            func.sum(
                RawMaterial.cost_per_unit
                * RawMaterialInventory.current_stock
                * HOLDING_COST_RATE
                / 12
            )
        )
        .join(RawMaterialInventory, RawMaterialInventory.material_id == RawMaterial.id)
        .scalar()
        or 0
    )

    gross_profit = total_revenue - total_cogs
    return {
        "total_revenue": round(total_revenue, 2),
        "total_cogs": round(total_cogs, 2),
        "total_holding_cost_monthly": round(total_holding, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round((gross_profit / total_revenue * 100), 1) if total_revenue > 0 else 0,
        "potential_savings": round(total_holding * 0.2, 2),
    }
