"""Tests for demand forecasting models."""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta


def _make_series(n: int = 60) -> pd.DataFrame:
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    values = [100 + 10 * np.sin(i / 7) + np.random.normal(0, 5) for i in range(n)]
    return pd.DataFrame({"ds": [str(d) for d in dates], "y": values})


def test_demand_forecaster_fit_predict():
    from models.forecasting.demand_forecast import DemandForecaster
    df = _make_series(60)
    forecaster = DemandForecaster()
    forecaster.fit(df)
    result = forecaster.predict(periods=14)
    assert len(result) == 14
    assert all("date" in r and "forecast" in r for r in result)
    assert all(r["forecast"] >= 0 for r in result)


def test_demand_forecaster_weekly_summary():
    from models.forecasting.demand_forecast import DemandForecaster
    df = _make_series(60)
    forecaster = DemandForecaster()
    forecaster.fit(df)
    weekly = forecaster.weekly_summary(periods=28)
    assert len(weekly) == 4
    for week in weekly:
        assert "week" in week and "revenue" in week


def test_forecaster_confidence_intervals():
    from models.forecasting.demand_forecast import DemandForecaster
    df = _make_series(60)
    forecaster = DemandForecaster()
    forecaster.fit(df)
    result = forecaster.predict(periods=7)
    for r in result:
        assert r["ci_lower"] <= r["forecast"] <= r["ci_upper"]


def test_forecaster_predict_without_fit():
    from models.forecasting.demand_forecast import DemandForecaster
    forecaster = DemandForecaster()
    with pytest.raises(RuntimeError):
        forecaster.predict()


def test_forecaster_product_id():
    from models.forecasting.demand_forecast import DemandForecaster
    df = _make_series(60)
    forecaster = DemandForecaster(product_id=42)
    forecaster.fit(df)
    assert forecaster.product_id == 42
