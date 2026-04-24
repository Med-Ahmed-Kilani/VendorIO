from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from backend.models.order import Order, OrderItem
from backend.models.product import Product
from backend.models.customer import Customer
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_kpi_metrics(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    base_q = db.query(Order).filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date,
        Order.status == "completed",
    )

    total_revenue = float(base_q.with_entities(func.sum(Order.total_amount)).scalar() or 0)
    order_count = base_q.count()
    avg_order_value = total_revenue / order_count if order_count > 0 else 0

    total_customers = base_q.with_entities(
        func.count(distinct(Order.customer_id))
    ).filter(Order.customer_id.isnot(None)).scalar() or 0

    repeat_customers = (
        db.query(func.count(distinct(Order.customer_id)))
        .filter(
            Order.customer_id.isnot(None),
            Order.order_date >= start_date,
            Order.order_date <= end_date,
        )
        .group_by(Order.customer_id)
        .having(func.count(Order.id) > 1)
        .count()
    )
    repeat_rate = repeat_customers / total_customers if total_customers > 0 else 0

    # Top products by revenue
    top_products = (
        db.query(
            Product.id,
            Product.name,
            Product.category,
            func.sum(OrderItem.line_total).label("revenue"),
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status == "completed",
        )
        .group_by(Product.id, Product.name, Product.category)
        .order_by(func.sum(OrderItem.line_total).desc())
        .limit(5)
        .all()
    )

    bottom_products = (
        db.query(
            Product.id,
            Product.name,
            Product.category,
            func.sum(OrderItem.line_total).label("revenue"),
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status == "completed",
        )
        .group_by(Product.id, Product.name, Product.category)
        .order_by(func.sum(OrderItem.line_total).asc())
        .limit(5)
        .all()
    )

    def _product_row(row) -> dict:
        return {
            "product_id": row.id,
            "product_name": row.name,
            "category": row.category,
            "revenue": round(float(row.revenue or 0), 2),
            "units_sold": int(row.units_sold or 0),
        }

    # Estimate profit using avg margin across all products
    products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    margins = [p.margin for p in products if p.margin is not None]
    avg_margin = sum(margins) / len(margins) if margins else 0.3
    estimated_profit = total_revenue * avg_margin

    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(estimated_profit, 2),
        "order_count": order_count,
        "avg_order_value": round(avg_order_value, 2),
        "total_customers": total_customers,
        "repeat_customer_rate": round(repeat_rate, 3),
        "top_products": [_product_row(r) for r in top_products],
        "bottom_products": [_product_row(r) for r in bottom_products],
    }


def get_customer_segments(db: Session) -> list[dict]:
    customers = db.query(Customer).all()
    if not customers:
        return []

    segments = []
    for c in customers:
        aov = (c.total_spent / c.order_count) if c.order_count > 0 else 0
        if c.order_count >= 5:
            segment = "loyal"
        elif c.order_count >= 2:
            segment = "returning"
        else:
            segment = "new"
        segments.append({
            "customer_id": c.id,
            "email": c.email,
            "total_spent": float(c.total_spent or 0),
            "order_count": c.order_count,
            "avg_order_value": round(float(aov), 2),
            "segment": segment,
        })
    return segments


def get_revenue_trend(
    db: Session, start_date: datetime, end_date: datetime
) -> list[dict]:
    rows = (
        db.query(
            func.date(Order.order_date).label("date"),
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .filter(
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status == "completed",
        )
        .group_by(func.date(Order.order_date))
        .order_by(func.date(Order.order_date))
        .all()
    )
    return [
        {"date": str(r.date), "revenue": round(float(r.revenue or 0), 2), "orders": r.orders}
        for r in rows
    ]
