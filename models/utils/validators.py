"""Data validation utilities for ML model inputs."""
import pandas as pd


def validate_time_series(df: pd.DataFrame, min_periods: int = 14) -> tuple[bool, str]:
    """Validate a time-series DataFrame before fitting a model.

    Args:
        df: DataFrame with 'ds' and 'y' columns.
        min_periods: Minimum number of data points required.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if df is None or df.empty:
        return False, "DataFrame is empty"
    if "ds" not in df.columns or "y" not in df.columns:
        return False, "DataFrame must have 'ds' and 'y' columns"
    if len(df) < min_periods:
        return False, f"Need at least {min_periods} data points, got {len(df)}"
    if df["y"].isna().all():
        return False, "All 'y' values are NaN"
    if (df["y"] < 0).any():
        return False, "Negative values in 'y' column"
    return True, ""


def validate_positive(value: float, name: str) -> None:
    """Raise ValueError if value is not positive.

    Args:
        value: Number to validate.
        name: Variable name for error message.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_inventory_inputs(
    current_stock: int, avg_daily_demand: float, lead_time_days: int
) -> tuple[bool, str]:
    """Validate inputs for inventory calculations.

    Args:
        current_stock: Current stock level.
        avg_daily_demand: Average daily units sold.
        lead_time_days: Supplier lead time.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if current_stock < 0:
        return False, "current_stock cannot be negative"
    if avg_daily_demand < 0:
        return False, "avg_daily_demand cannot be negative"
    if lead_time_days <= 0:
        return False, "lead_time_days must be positive"
    return True, ""
