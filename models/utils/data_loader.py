"""Load historical data from DB or CSV for ML model training."""
from pathlib import Path
from typing import Optional
import pandas as pd


def load_from_csv(path: str | Path, date_col: str = "InvoiceDate") -> pd.DataFrame:
    """Load the Online Retail CSV and normalise column names.

    Args:
        path: Path to the CSV file.
        date_col: Name of the date column.

    Returns:
        Cleaned DataFrame.
    """
    df = pd.read_csv(path, encoding="ISO-8859-1", low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    # Drop rows with missing invoice or quantity
    df = df.dropna(subset=["InvoiceNo", "Quantity"])
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]
    return df


def build_daily_revenue(df: pd.DataFrame, date_col: str = "InvoiceDate") -> pd.DataFrame:
    """Aggregate raw transaction data into daily revenue.

    Args:
        df: Raw transaction DataFrame.
        date_col: Name of the date column.

    Returns:
        DataFrame with columns: ds (date), y (revenue).
    """
    df = df.copy()
    df["revenue"] = df["Quantity"] * df["UnitPrice"]
    df["date"] = df[date_col].dt.date
    daily = df.groupby("date")["revenue"].sum().reset_index()
    daily.columns = ["ds", "y"]
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily.sort_values("ds").reset_index(drop=True)


def build_product_demand(df: pd.DataFrame, stock_code: str, date_col: str = "InvoiceDate") -> Optional[pd.DataFrame]:
    """Build daily demand series for a single product.

    Args:
        df: Raw transaction DataFrame.
        stock_code: Product stock code identifier.
        date_col: Name of the date column.

    Returns:
        DataFrame with ds, y columns or None if product not found.
    """
    subset = df[df["StockCode"] == stock_code].copy()
    if subset.empty:
        return None
    subset["date"] = subset[date_col].dt.date
    daily = subset.groupby("date")["Quantity"].sum().reset_index()
    daily.columns = ["ds", "y"]
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily.sort_values("ds").reset_index(drop=True)
