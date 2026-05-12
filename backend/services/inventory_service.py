import math
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.product import Product
from backend.models.order import OrderItem, Order
from backend.schemas.inventory import InventoryStatusItem, InventoryHealthResponse
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

HOLDING_COST_RATE = settings.holding_cost_rate  # fraction of unit cost per year
ORDERING_COST = settings.ordering_cost  # $ per order


def _avg_daily_sales(db: Session, product_id: int, lookback_days: int = 90) -> float:
    since = datetime.utcnow() - timedelta(days=lookback_days)
    result = (
        db.query(func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(OrderItem.product_id == product_id, Order.order_date >= since)
        .scalar()
    )
    total_qty = result or 0
    return total_qty / lookback_days


def calculate_reorder_point(avg_daily_demand: float, lead_time_days: int) -> float:
    """Calculate reorder point for inventory.

    Args:
        avg_daily_demand: Average units sold per day.
        lead_time_days: Days to receive new shipment from supplier.

    Returns:
        Reorder point in units.

    Example:
        >>> calculate_reorder_point(5.0, 7)
        35.0
    """
    return avg_daily_demand * lead_time_days


def calculate_eoq(annual_demand: float, ordering_cost: float, holding_cost_per_unit: float) -> float:
    """Calculate Economic Order Quantity.

    Args:
        annual_demand: Total units demanded per year.
        ordering_cost: Fixed cost per order placed.
        holding_cost_per_unit: Annual holding cost per unit.

    Returns:
        Optimal order quantity.
    """
    if holding_cost_per_unit <= 0 or annual_demand <= 0:
        return 0.0
    return math.sqrt(2 * annual_demand * ordering_cost / holding_cost_per_unit)


def days_to_stockout(current_stock: int, avg_daily_demand: float) -> Optional[float]:
    if avg_daily_demand <= 0:
        return None
    return current_stock / avg_daily_demand


def classify_turnover(turnover_rate: float, all_rates: list[float]) -> str:
    if not all_rates:
        return "unknown"
    sorted_rates = sorted(all_rates)
    p25 = sorted_rates[int(len(sorted_rates) * 0.25)]
    p75 = sorted_rates[int(len(sorted_rates) * 0.75)]
    if turnover_rate <= p25:
        return "slow"
    if turnover_rate >= p75:
        return "fast"
    return "average"


def get_inventory_status(db: Session) -> list[InventoryStatusItem]:
    products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    if not products:
        return []

    daily_sales = {p.id: _avg_daily_sales(db, p.id) for p in products}
    turnover_rates = {}
    for p in products:
        avg_daily = daily_sales.get(p.id, 0)
        if p.current_stock > 0 and avg_daily > 0:
            turnover_rates[p.id] = (avg_daily * 365) / p.current_stock
        else:
            turnover_rates[p.id] = 0.0

    all_rates = list(turnover_rates.values())
    results = []
    for p in products:
        avg_daily = daily_sales.get(p.id, 0)
        dts = days_to_stockout(p.current_stock, avg_daily)
        reorder = p.reorder_point or calculate_reorder_point(avg_daily, p.lead_time_days)
        holding_cost_monthly = (
            float(p.cost_per_unit or p.unit_price) * p.current_stock * HOLDING_COST_RATE / 12
            if p.current_stock > 0
            else 0.0
        )

        if dts is not None and dts < 7:
            status = "critical"
        elif dts is not None and dts < 14:
            status = "warning"
        else:
            status = "ok"

        results.append(
            InventoryStatusItem(
                product_id=p.id,
                product_name=p.name,
                category=p.category,
                current_stock=p.current_stock,
                reorder_point=p.reorder_point,
                days_to_stockout=round(dts, 1) if dts is not None else None,
                turnover_rate=round(turnover_rates[p.id], 2),
                holding_cost_monthly=round(holding_cost_monthly, 2),
                status=status,
                needs_reorder=p.current_stock <= reorder,
            )
        )
    return results


def get_product_health(db: Session, product_id: int) -> Optional[InventoryHealthResponse]:
    p = db.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
    if not p:
        return None

    avg_daily = _avg_daily_sales(db, product_id)
    dts = days_to_stockout(p.current_stock, avg_daily)
    holding_cost_monthly = (
        float(p.cost_per_unit or p.unit_price) * p.current_stock * HOLDING_COST_RATE / 12
    )
    annual_demand = avg_daily * 365
    holding_per_unit = float(p.cost_per_unit or p.unit_price) * HOLDING_COST_RATE
    eoq = calculate_eoq(annual_demand, ORDERING_COST, holding_per_unit)

    all_products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    all_rates = []
    for ap in all_products:
        ads = _avg_daily_sales(db, ap.id)
        if ap.current_stock > 0 and ads > 0:
            all_rates.append((ads * 365) / ap.current_stock)

    my_rate = (avg_daily * 365 / p.current_stock) if p.current_stock > 0 else 0.0
    rank = classify_turnover(my_rate, all_rates)

    if dts is not None and dts < 7:
        status = "critical"
    elif dts is not None and dts < 14:
        status = "warning"
    else:
        status = "ok"

    return InventoryHealthResponse(
        product_id=p.id,
        product_name=p.name,
        current_stock=p.current_stock,
        days_to_stockout=round(dts, 1) if dts is not None else None,
        holding_cost_monthly=round(holding_cost_monthly, 2),
        turnover_rate=round(my_rate, 2),
        turnover_rank=rank,
        reorder_point=p.reorder_point,
        economic_order_qty=round(eoq, 0) if eoq else None,
        status=status,
    )
