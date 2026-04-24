"""Customer segmentation using RFM (Recency, Frequency, Monetary) scoring."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
import pandas as pd
import numpy as np


@dataclass
class CustomerRecord:
    customer_id: int
    last_order_date: date
    order_count: int
    total_spent: float


def rfm_score(customers: list[CustomerRecord], reference_date: Optional[date] = None) -> pd.DataFrame:
    """Compute RFM scores and assign segments.

    Args:
        customers: List of CustomerRecord objects.
        reference_date: Date to calculate recency from (default: today).

    Returns:
        DataFrame with customer_id, recency_days, frequency, monetary, rfm_score, segment.
    """
    if not customers:
        return pd.DataFrame()

    ref = reference_date or date.today()
    records = []
    for c in customers:
        recency = (ref - c.last_order_date).days if c.last_order_date else 999
        records.append({
            "customer_id": c.customer_id,
            "recency_days": recency,
            "frequency": c.order_count,
            "monetary": float(c.total_spent or 0),
        })
    df = pd.DataFrame(records)

    # Quintile scoring (1-5, higher = better)
    df["r_score"] = pd.qcut(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1], duplicates="drop")
    df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    df["rfm_score"] = df[["r_score", "f_score", "m_score"]].apply(
        lambda x: int(x["r_score"]) + int(x["f_score"]) + int(x["m_score"]), axis=1
    )

    def _segment(row) -> str:
        if row["rfm_score"] >= 13:
            return "champions"
        if row["rfm_score"] >= 10:
            return "loyal"
        if row["rfm_score"] >= 7:
            return "potential_loyal"
        if row["r_score"] >= 4 and row["f_score"] <= 2:
            return "new_customers"
        if row["r_score"] <= 2:
            return "at_risk"
        return "needs_attention"

    df["segment"] = df.apply(_segment, axis=1)
    return df


def segment_summary(df: pd.DataFrame) -> list[dict]:
    """Aggregate RFM results into a segment summary.

    Args:
        df: Output of rfm_score().

    Returns:
        List of segment dicts with counts and averages.
    """
    if df.empty:
        return []
    grouped = df.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency_days=("recency_days", "mean"),
    ).reset_index()
    return grouped.to_dict(orient="records")
