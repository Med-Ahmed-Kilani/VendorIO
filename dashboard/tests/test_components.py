"""Light tests for dashboard utility functions."""
from datetime import date, datetime
from dashboard.utils.formatters import fmt_currency, fmt_pct, fmt_number, fmt_days, fmt_date


def test_fmt_currency_basic():
    assert fmt_currency(1234.5) == "$1,235"


def test_fmt_currency_with_decimals():
    assert fmt_currency(1234.5, decimals=2) == "$1,234.50"


def test_fmt_currency_none():
    assert fmt_currency(None) == "N/A"


def test_fmt_pct():
    assert fmt_pct(12.5) == "12.5%"


def test_fmt_pct_none():
    assert fmt_pct(None) == "N/A"


def test_fmt_number():
    assert fmt_number(1000) == "1,000"


def test_fmt_days_normal():
    assert fmt_days(10.0) == "10d"


def test_fmt_days_none():
    assert fmt_days(None) == "∞"


def test_fmt_date_date():
    d = date(2024, 4, 15)
    assert fmt_date(d) == "Apr 15, 2024"


def test_fmt_date_none():
    assert fmt_date(None) == ""
