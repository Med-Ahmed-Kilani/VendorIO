from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.services import metrics_service, cost_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/kpi")
def get_kpis(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """Aggregated KPI metrics: revenue, profit, AOV, repeat customer rate, top/bottom products."""
    return metrics_service.get_kpi_metrics(db, start_date=start_date, end_date=end_date)


@router.get("/revenue-trend")
def revenue_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Daily revenue trend for the last N days."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return metrics_service.get_revenue_trend(db, start_date=start, end_date=end)


@router.get("/customer-segments")
def customer_segments(db: Session = Depends(get_db)) -> list[dict]:
    """Customer cohorts segmented by purchase behaviour."""
    return metrics_service.get_customer_segments(db)


@router.get("/profitability")
def profitability(db: Session = Depends(get_db)) -> list[dict]:
    """Margin analysis ranked by gross profit."""
    return cost_service.get_product_profitability(db)


@router.get("/cost-summary")
def cost_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """High-level cost breakdown: COGS, holding costs, gross profit, potential savings."""
    return cost_service.get_cost_summary(db, start_date=start_date, end_date=end_date)
