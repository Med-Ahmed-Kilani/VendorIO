import re
from sqlalchemy.orm import Session
from backend.models.raw_material import RawMaterial
from backend.services.inventory_service import (
    _material_daily_consumption,
    _current_stock,
    days_to_stockout,
    HOLDING_COST_RATE,
    ORDERING_COST,
    calculate_eoq,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

URGENCY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def generate_recommendations(db: Session, limit: int = 20) -> list[dict]:
    materials = db.query(RawMaterial).all()
    recommendations = []

    daily_consumption = {m.id: _material_daily_consumption(db, m.id) for m in materials}
    stock_levels = {m.id: _current_stock(db, m.id) for m in materials}

    turnover_rates = {}
    for m in materials:
        adc = daily_consumption.get(m.id, 0)
        stock = stock_levels.get(m.id, 0)
        if stock > 0 and adc > 0:
            turnover_rates[m.id] = (adc * 365) / stock
        else:
            turnover_rates[m.id] = 0.0

    all_rates = list(turnover_rates.values())
    threshold_slow = 0
    if all_rates:
        sorted_rates = sorted(all_rates)
        threshold_slow = sorted_rates[max(0, int(len(sorted_rates) * 0.25))]

    for m in materials:
        adc = daily_consumption.get(m.id, 0)
        stock = stock_levels.get(m.id, 0)
        dts = days_to_stockout(stock, adc)
        unit_cost = float(m.cost_per_unit or 0)
        holding_cost_monthly = unit_cost * stock * HOLDING_COST_RATE / 12
        reorder = m.reorder_point or (adc * m.lead_time_days)

        # Rule 1: Stockout risk
        if dts is not None and dts <= 14:
            urgency = "critical" if dts <= 7 else "high"
            annual_demand = adc * 365
            eoq = calculate_eoq(annual_demand, ORDERING_COST, unit_cost * HOLDING_COST_RATE)
            reorder_qty = max(int(eoq), int(reorder * 2), 1)
            recommendations.append({
                "type": "stockout_risk",
                "product_id": m.id,
                "product_name": m.name,
                "days_remaining": round(dts, 1),
                "action": f"Reorder {reorder_qty} {m.unit or 'units'} of '{m.name}' immediately",
                "impact": "Avoid production stoppage from ingredient shortage",
                "urgency": urgency,
            })

        # Rule 2: Slow movers
        if turnover_rates.get(m.id, 0) <= threshold_slow and stock > 0:
            savings_annual = holding_cost_monthly * 12
            recommendations.append({
                "type": "slow_mover",
                "product_id": m.id,
                "product_name": m.name,
                "turnover_rate": round(turnover_rates.get(m.id, 0), 2),
                "action": f"Reduce order frequency for '{m.name}' — low consumption rate",
                "impact": f"Reduce holding cost by ${savings_annual:.0f}/year",
                "urgency": "medium",
            })

        # Rule 3: Overstock
        if adc > 0 and dts is not None and dts > 180:
            recommendations.append({
                "type": "overstock",
                "product_id": m.id,
                "product_name": m.name,
                "days_to_stockout": round(dts, 0),
                "action": f"Reduce next order for '{m.name}' — {dts:.0f} days of stock on hand",
                "impact": f"Free up ${holding_cost_monthly:.0f}/month in holding costs",
                "urgency": "low",
            })

    # Rule 4: High-velocity materials — suggest bulk orders
    velocity_vals = sorted(daily_consumption.values(), reverse=True)
    if velocity_vals:
        top_threshold = velocity_vals[max(0, int(len(velocity_vals) * 0.1))]
        for m in materials:
            adc = daily_consumption.get(m.id, 0)
            if adc >= top_threshold and adc > 0:
                unit_cost = float(m.cost_per_unit or 0)
                annual_demand = adc * 365
                eoq = calculate_eoq(annual_demand, ORDERING_COST, unit_cost * HOLDING_COST_RATE)
                savings = unit_cost * eoq * 0.05
                if savings > 50:
                    recommendations.append({
                        "type": "bulk_order",
                        "product_id": m.id,
                        "product_name": m.name,
                        "action": f"Place bulk order of {int(eoq)} {m.unit or 'units'} for '{m.name}' (EOQ)",
                        "impact": f"Save ${savings:.0f} with 5% bulk discount",
                        "urgency": "low",
                    })

    recommendations.sort(key=lambda r: URGENCY_ORDER.get(r["urgency"], 99))
    return recommendations[:limit]


def get_potential_savings(recommendations: list[dict]) -> float:
    total = 0.0
    for r in recommendations:
        match = re.search(r"\$([0-9,]+)", r.get("impact", ""))
        if match:
            total += float(match.group(1).replace(",", ""))
    return round(total, 2)
