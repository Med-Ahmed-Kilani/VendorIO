"""Product-level and aggregate demand forecasting."""
from typing import Optional
import pandas as pd
import numpy as np
from models.forecasting.time_series import ARIMAForecaster


class DemandForecaster:
    """Forecast revenue or product demand using ARIMA with confidence intervals.

    Args:
        product_id: Optional product ID (None = aggregate revenue forecast).
    """

    def __init__(self, product_id: Optional[int] = None) -> None:
        self.product_id = product_id
        self._forecaster: Optional[ARIMAForecaster] = None
        self._series: Optional[pd.Series] = None
        self.model_name = "ARIMA"
        self.mape: Optional[float] = None

    def fit(self, historical_data: pd.DataFrame) -> "DemandForecaster":
        """Fit forecasting model on historical data.

        Args:
            historical_data: DataFrame with columns 'ds' (date string) and 'y' (value).

        Returns:
            self
        """
        df = historical_data.copy()
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.set_index("ds").sort_index()
        # Fill missing dates with 0
        full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")
        series = df["y"].reindex(full_range, fill_value=0).astype(float)
        self._series = series
        self._forecaster = ARIMAForecaster()
        self._forecaster.fit(series)
        self.mape = self._forecaster.mape
        return self

    def predict(self, periods: int = 28) -> list[dict]:
        """Generate a forecast for N days ahead.

        Args:
            periods: Days to forecast ahead.

        Returns:
            List of {date, forecast, ci_lower, ci_upper} dicts.
        """
        if self._forecaster is None:
            raise RuntimeError("Call fit() first")
        return self._forecaster.predict(periods=periods)

    def weekly_summary(self, periods: int = 28) -> list[dict]:
        """Aggregate daily forecast into weekly buckets.

        Args:
            periods: Number of days to forecast (should be multiple of 7).

        Returns:
            List of weekly {week_start, forecast, ci_lower, ci_upper} dicts.
        """
        daily = self.predict(periods=periods)
        weekly = []
        for i in range(0, len(daily), 7):
            chunk = daily[i : i + 7]
            if not chunk:
                break
            weekly.append({
                "week": chunk[0]["date"],
                "revenue": round(sum(d["forecast"] for d in chunk), 2),
                "ci_lower": round(sum(d["ci_lower"] for d in chunk), 2),
                "ci_upper": round(sum(d["ci_upper"] for d in chunk), 2),
            })
        return weekly
