"""ARIMA-based time series forecasting wrapper."""
from typing import Optional
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_percentage_error


class ARIMAForecaster:
    """Thin ARIMA wrapper that auto-selects order via AIC grid search."""

    DEFAULT_ORDERS = [(1, 1, 1), (2, 1, 1), (1, 1, 2), (2, 1, 2)]

    def __init__(self, order: tuple[int, int, int] = (1, 1, 1)) -> None:
        self.order = order
        self._model = None
        self._fitted = None
        self.mape: Optional[float] = None

    def fit(self, series: pd.Series) -> "ARIMAForecaster":
        """Fit ARIMA on a pandas Series indexed by date.

        Args:
            series: Time-series of values (revenue or quantity), DatetimeIndex.

        Returns:
            self
        """
        best_aic = float("inf")
        best_order = self.order
        for order in self.DEFAULT_ORDERS:
            try:
                m = ARIMA(series, order=order).fit()
                if m.aic < best_aic:
                    best_aic = m.aic
                    best_order = order
            except Exception:
                continue
        self.order = best_order
        self._fitted = ARIMA(series, order=best_order).fit()
        # In-sample MAPE on last 20% of data
        n = len(series)
        holdout_n = max(7, int(n * 0.2))
        if n > holdout_n + 7:
            train = series.iloc[:-holdout_n]
            test = series.iloc[-holdout_n:]
            m_eval = ARIMA(train, order=best_order).fit()
            preds = m_eval.forecast(steps=holdout_n)
            try:
                self.mape = round(float(mean_absolute_percentage_error(test, preds)), 4)
            except Exception:
                self.mape = None
        return self

    def predict(self, periods: int = 28) -> list[dict]:
        """Forecast N periods ahead.

        Args:
            periods: Number of days to forecast.

        Returns:
            List of dicts with date, forecast, ci_lower, ci_upper.
        """
        if self._fitted is None:
            raise RuntimeError("Call fit() before predict()")
        fc = self._fitted.get_forecast(steps=periods)
        mean = fc.predicted_mean
        ci = fc.conf_int(alpha=0.2)  # 80% CI
        results = []
        for i, (date, val) in enumerate(mean.items()):
            results.append({
                "date": str(date.date()) if hasattr(date, "date") else str(date),
                "forecast": round(max(float(val), 0), 2),
                "ci_lower": round(max(float(ci.iloc[i, 0]), 0), 2),
                "ci_upper": round(max(float(ci.iloc[i, 1]), 0), 2),
            })
        return results
