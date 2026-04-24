"""Number and date formatting utilities."""
from datetime import date, datetime
from typing import Optional


def fmt_currency(value: Optional[float], decimals: int = 0) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.{decimals}f}"


def fmt_pct(value: Optional[float], decimals: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def fmt_number(value: Optional[float | int], decimals: int = 0) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_days(value: Optional[float]) -> str:
    if value is None:
        return "∞"
    return f"{value:.0f}d"


def fmt_date(d: Optional[date | datetime | str]) -> str:
    if d is None:
        return ""
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d)
        except ValueError:
            return d
    return d.strftime("%b %d, %Y")


def delta_color(current: float, previous: float) -> str:
    """Return 'normal' (green up), 'inverse' (red up) based on direction."""
    return "normal" if current >= previous else "inverse"
