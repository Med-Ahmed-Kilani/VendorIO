from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.product import Product
from backend.models.order import Order, OrderItem
from backend.services.inventory_service import (
    _avg_daily_sales,
    days_to_stockout,
    HOLDING_COST_RATE,
    ORDERING_COST,
    calculate_eoq,
)
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

URGENCY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def generate_recommendations(db: Session, limit: int = 20) -> list[dict]:
    products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    recommendations = []

    # Pre-compute daily sales and turnover for all products
    daily_sales = {p.id: _avg_daily_sales(db, p.id) for p in products}
    turnover_rates = {}
    for p in products:
        ads = daily_sales.get(p.id, 0)
        if p.current_stock > 0 and ads > 0:
            turnover_rates[p.id] = (ads * 365) / p.current_stock
        else:
            turnover_rates[p.id] = 0.0

    all_rates = list(turnover_rates.values())
    if all_rates:
        sorted_rates = sorted(all_rates)
        threshold_slow = sorted_rates[max(0, int(len(sorted_rates) * 0.25))]
    else:
        threshold_slow = 0

    for p in products:
        ads = daily_sales.get(p.id, 0)
        dts = days_to_stockout(p.current_stock, ads)
        holding_cost_monthly = (
            float(p.cost_per_unit or p.unit_price) * p.current_stock * HOLDING_COST_RATE / 12
        )
        reorder = p.reorder_point or (ads * p.lead_time_days)

        # Rule 1: Stockout risk
        if dts is not None and dts <= 14:
            urgency = "critical" if dts <= 7 else "high"
            annual_demand = ads * 365
            eoq = calculate_eoq(
                annual_demand,
                ORDERING_COST,
                float(p.cost_per_unit or p.unit_price) * HOLDING_COST_RATE,
            )
            reorder_qty = max(int(eoq), int(reorder * 2), 1)
            recommendations.append({
                "type": "stockout_risk",
                "product_id": p.id,
                "product_name": p.name,
                "days_remaining": round(dts, 1),
                "action": f"Reorder {reorder_qty} units of '{p.name}' immediately",
                "impact": "Avoid lost sales and customer dissatisfaction",
                "urgency": urgency,
            })

        # Rule 2: Slow movers
        if turnover_rates.get(p.id, 0) <= threshold_slow and p.current_stock > 0:
            savings_annual = holding_cost_monthly * 12
            recommendations.append({
                "type": "slow_mover",
                "product_id": p.id,
                "product_name": p.name,
                "turnover_rate": round(turnover_rates.get(p.id, 0), 2),
                "action": f"Bundle '{p.name}' with fast-movers or apply 10-15% discount",
                "impact": f"Reduce holding cost by ${savings_annual:.0f}/year",
                "urgency": "medium",
            })

        # Rule 3: Overstock — too much stock relative to velocity
        if ads > 0 and dts is not None and dts > 180:
            recommendations.append({
                "type": "overstock",
                "product_id": p.id,
                "product_name": p.name,
                "days_to_stockout": round(dts, 0),
                "action": f"Reduce next order size for '{p.name}' — {dts:.0f} days of stock on hand",
                "impact": f"Free up ${holding_cost_monthly:.0f}/month in holding costs",
                "urgency": "low",
            })

    # Rule 4: High-velocity products — check if they need bulk order
    velocity_threshold = sorted(daily_sales.values(), reverse=True)
    if velocity_threshold:
        top_10_pct_threshold = velocity_threshold[max(0, int(len(velocity_threshold) * 0.1))]
        for p in products:
            ads = daily_sales.get(p.id, 0)
            if ads >= top_10_pct_threshold and ads > 0:
                annual_demand = ads * 365
                eoq = calculate_eoq(
                    annual_demand,
                    ORDERING_COST,
                    float(p.cost_per_unit or p.unit_price) * HOLDING_COST_RATE,
                )
                savings = (p.cost_per_unit or p.unit_price) * eoq * 0.05  # 5% bulk discount
                if savings > 50:
                    recommendations.append({
                        "type": "bulk_order",
                        "product_id": p.id,
                        "product_name": p.name,
                        "action": f"Place bulk order of {int(eoq)} units for '{p.name}' (EOQ)",
                        "impact": f"Save ${savings:.0f} with 5% bulk discount",
                        "urgency": "low",
                    })

    recommendations.sort(key=lambda r: URGENCY_ORDER.get(r["urgency"], 99))
    return recommendations[:limit]


def get_potential_savings(recommendations: list[dict]) -> float:
    total = 0.0
    for r in recommendations:
        impact = r.get("impact", "")
        # Extract dollar amount from impact string
        import re
        match = re.search(r"\$([0-9,]+)", impact)
        if match:
            total += float(match.group(1).replace(",", ""))
    return round(total, 2)
