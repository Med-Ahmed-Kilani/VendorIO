from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.product import Product
from backend.models.order import Order, OrderItem
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

HOLDING_COST_RATE = settings.holding_cost_rate


def get_product_profitability(db: Session) -> list[dict]:
    products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    result = []
    for p in products:
        total_sold = (
            db.query(func.sum(OrderItem.quantity))
            .filter(OrderItem.product_id == p.id)
            .scalar()
            or 0
        )
        revenue = total_sold * float(p.unit_price)
        cogs = total_sold * float(p.cost_per_unit or 0)
        holding_cost_annual = (
            float(p.cost_per_unit or p.unit_price) * p.current_stock * HOLDING_COST_RATE
        )
        gross_profit = revenue - cogs
        margin = (gross_profit / revenue) if revenue > 0 else None

        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "category": p.category,
            "unit_price": float(p.unit_price),
            "cost_per_unit": float(p.cost_per_unit) if p.cost_per_unit else None,
            "total_units_sold": total_sold,
            "total_revenue": round(revenue, 2),
            "total_cogs": round(cogs, 2),
            "holding_cost_annual": round(holding_cost_annual, 2),
            "gross_profit": round(gross_profit, 2),
            "margin_pct": round(margin * 100, 1) if margin is not None else None,
        })
    return sorted(result, key=lambda x: x["gross_profit"], reverse=True)


def get_cost_summary(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> dict:
    q = db.query(func.sum(Order.total_amount)).filter(Order.status == "completed")
    if start_date:
        q = q.filter(Order.order_date >= start_date)
    if end_date:
        q = q.filter(Order.order_date <= end_date)
    total_revenue = float(q.scalar() or 0)

    products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    total_cogs = 0.0
    total_holding = 0.0
    for p in products:
        qty_filter = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.product_id == p.id, Order.status == "completed"
        )
        if start_date:
            qty_filter = qty_filter.filter(Order.order_date >= start_date)
        if end_date:
            qty_filter = qty_filter.filter(Order.order_date <= end_date)
        sold = float(qty_filter.scalar() or 0)
        total_cogs += sold * float(p.cost_per_unit or 0)
        total_holding += float(p.cost_per_unit or p.unit_price) * p.current_stock * HOLDING_COST_RATE / 12

    gross_profit = total_revenue - total_cogs
    return {
        "total_revenue": round(total_revenue, 2),
        "total_cogs": round(total_cogs, 2),
        "total_holding_cost_monthly": round(total_holding, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round((gross_profit / total_revenue * 100), 1) if total_revenue > 0 else 0,
        "potential_savings": round(total_holding * 0.2, 2),  # 20% reduction estimate
    }
