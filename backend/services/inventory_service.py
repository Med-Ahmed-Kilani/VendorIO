import math
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.raw_material import RawMaterial, RawMaterialInventory
from backend.models.recipe import Recipe, RecipeItem
from backend.models.order import OrderItem, Order
from backend.schemas.inventory import InventoryStatusItem, InventoryHealthResponse
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

HOLDING_COST_RATE = settings.holding_cost_rate
ORDERING_COST = settings.ordering_cost


def _latest_order_date(db: Session) -> datetime:
    latest = db.query(func.max(Order.order_date)).scalar()
    return latest if latest else datetime.utcnow()


def _material_daily_consumption(db: Session, material_id: int, lookback_days: int = 90) -> float:
    """Estimate average daily consumption of a raw material from order history."""
    anchor = _latest_order_date(db)
    since = anchor - timedelta(days=lookback_days)

    # Sum: quantity_ordered × quantity_needed per unit across all recipes using this material
    result = (
        db.query(
            func.sum(OrderItem.quantity * RecipeItem.quantity_needed)
        )
        .join(RecipeItem, RecipeItem.recipe_id == OrderItem.recipe_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            RecipeItem.material_id == material_id,
            Order.order_date >= since,
        )
        .scalar()
    )
    return float(result or 0) / lookback_days


def calculate_reorder_point(avg_daily_demand: float, lead_time_days: int) -> float:
    return avg_daily_demand * lead_time_days


def calculate_eoq(annual_demand: float, ordering_cost: float, holding_cost_per_unit: float) -> float:
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


def _current_stock(db: Session, material_id: int) -> int:
    """Return live stock from raw_material_inventory (latest row per material)."""
    row = (
        db.query(RawMaterialInventory.current_stock)
        .filter(RawMaterialInventory.material_id == material_id)
        .order_by(RawMaterialInventory.id.desc())
        .first()
    )
    return int(row.current_stock) if row else 0


def get_inventory_status(db: Session) -> list[InventoryStatusItem]:
    materials = db.query(RawMaterial).all()
    if not materials:
        return []

    daily_consumption = {m.id: _material_daily_consumption(db, m.id) for m in materials}
    turnover_rates = {}
    for m in materials:
        stock = _current_stock(db, m.id)
        avg_daily = daily_consumption.get(m.id, 0)
        if stock > 0 and avg_daily > 0:
            turnover_rates[m.id] = (avg_daily * 365) / stock
        else:
            turnover_rates[m.id] = 0.0

    all_rates = list(turnover_rates.values())
    results = []
    for m in materials:
        stock = _current_stock(db, m.id)
        avg_daily = daily_consumption.get(m.id, 0)
        dts = days_to_stockout(stock, avg_daily)
        reorder = m.reorder_point or calculate_reorder_point(avg_daily, m.lead_time_days)
        holding_cost_monthly = (
            float(m.cost_per_unit or 0) * stock * HOLDING_COST_RATE / 12
            if stock > 0
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
                product_id=m.id,
                product_name=m.name,
                category=m.category,
                current_stock=stock,
                reorder_point=m.reorder_point,
                days_to_stockout=round(dts, 1) if dts is not None else None,
                turnover_rate=round(turnover_rates[m.id], 2),
                holding_cost_monthly=round(holding_cost_monthly, 2),
                status=status,
                needs_reorder=stock <= reorder,
            )
        )
    return results


def get_product_health(db: Session, material_id: int) -> Optional[InventoryHealthResponse]:
    m = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not m:
        return None

    stock = _current_stock(db, material_id)
    avg_daily = _material_daily_consumption(db, material_id)
    dts = days_to_stockout(stock, avg_daily)
    holding_cost_monthly = float(m.cost_per_unit or 0) * stock * HOLDING_COST_RATE / 12
    annual_demand = avg_daily * 365
    holding_per_unit = float(m.cost_per_unit or 0) * HOLDING_COST_RATE
    eoq = calculate_eoq(annual_demand, ORDERING_COST, holding_per_unit)

    all_materials = db.query(RawMaterial).all()
    all_rates = []
    for am in all_materials:
        s = _current_stock(db, am.id)
        ads = _material_daily_consumption(db, am.id)
        if s > 0 and ads > 0:
            all_rates.append((ads * 365) / s)

    my_rate = (avg_daily * 365 / stock) if stock > 0 else 0.0
    rank = classify_turnover(my_rate, all_rates)

    if dts is not None and dts < 7:
        status = "critical"
    elif dts is not None and dts < 14:
        status = "warning"
    else:
        status = "ok"

    return InventoryHealthResponse(
        product_id=m.id,
        product_name=m.name,
        current_stock=stock,
        days_to_stockout=round(dts, 1) if dts is not None else None,
        holding_cost_monthly=round(holding_cost_monthly, 2),
        turnover_rate=round(my_rate, 2),
        turnover_rank=rank,
        reorder_point=m.reorder_point,
        economic_order_qty=round(eoq, 0) if eoq else None,
        status=status,
    )
