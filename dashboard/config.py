import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

COLORS = {
    "primary": "#2563EB",
    "success": "#16A34A",
    "warning": "#CA8A04",
    "danger": "#DC2626",
    "neutral": "#6B7280",
    "background": "#F8FAFC",
}

STATUS_COLORS = {
    "ok": COLORS["success"],
    "warning": COLORS["warning"],
    "critical": COLORS["danger"],
}

URGENCY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

PAGE_TITLE = "VendorIO"
PAGE_ICON = "📦"
