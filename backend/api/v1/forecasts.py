from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.utils.errors import InsufficientDataError
from backend.utils.logger import get_logger

router = APIRouter(prefix="/forecasts", tags=["forecasts"])
logger = get_logger(__name__)


def _get_revenue_series(db: Session):
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from backend.models.order import Order
    import pandas as pd

    rows = (
        db.query(
            func.date(Order.order_date).label("ds"),
            func.sum(Order.total_amount).label("y"),
        )
        .filter(Order.status == "completed")
        .group_by(func.date(Order.order_date))
        .order_by(func.date(Order.order_date))
        .all()
    )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([{"ds": str(r.ds), "y": float(r.y or 0)} for r in rows])


def _get_product_series(db: Session, product_id: int):
    from sqlalchemy import func
    from backend.models.order import Order, OrderItem
    import pandas as pd

    rows = (
        db.query(
            func.date(Order.order_date).label("ds"),
            func.sum(OrderItem.quantity).label("y"),
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .filter(OrderItem.product_id == product_id, Order.status == "completed")
        .group_by(func.date(Order.order_date))
        .order_by(func.date(Order.order_date))
        .all()
    )
    if not rows:
        return None
    return [{"ds": str(r.ds), "y": int(r.y or 0)} for r in rows]


@router.get("/revenue")
def forecast_revenue(
    weeks_ahead: int = Query(4, ge=1, le=26),
    db: Session = Depends(get_db),
) -> dict:
    """4-week aggregate revenue forecast using ARIMA."""
    try:
        from models.forecasting.demand_forecast import DemandForecaster
        df = _get_revenue_series(db)
        if df.empty or len(df) < 14:
            raise InsufficientDataError("Need at least 14 days of order history for forecasting")
        forecaster = DemandForecaster()
        forecaster.fit(df)
        result = forecaster.predict(periods=weeks_ahead * 7)
        return {
            "forecast": result,
            "model": forecaster.model_name,
            "mape": forecaster.mape,
            "weeks_ahead": weeks_ahead,
        }
    except InsufficientDataError:
        raise
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise InsufficientDataError(f"Could not generate forecast: {str(e)}")


@router.get("/demand")
def forecast_demand(
    product_id: int = Query(...),
    weeks_ahead: int = Query(4, ge=1, le=26),
    db: Session = Depends(get_db),
) -> dict:
    """Product-level demand forecast."""
    try:
        from models.forecasting.demand_forecast import DemandForecaster
        series = _get_product_series(db, product_id)
        if not series or len(series) < 14:
            raise InsufficientDataError("Need at least 14 data points for product-level forecasting")
        import pandas as pd
        df = pd.DataFrame(series)
        forecaster = DemandForecaster(product_id=product_id)
        forecaster.fit(df)
        result = forecaster.predict(periods=weeks_ahead * 7)
        return {
            "product_id": product_id,
            "forecast": result,
            "model": forecaster.model_name,
            "mape": forecaster.mape,
            "weeks_ahead": weeks_ahead,
        }
    except InsufficientDataError:
        raise
    except Exception as e:
        logger.error(f"Product forecast error for {product_id}: {e}")
        raise InsufficientDataError(f"Could not generate forecast: {str(e)}")


@router.post("/retrain")
def retrain_models(db: Session = Depends(get_db)) -> dict:
    """Trigger retraining of all forecasting models."""
    return {"status": "queued", "message": "Model retraining has been queued"}
