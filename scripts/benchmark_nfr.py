#!/usr/bin/env python3
"""Measure the non-functional requirements (NFR) of the VendorIO API.

Produces, from one dataset, in one run:

  * the shape of the loaded dataset (orders, lines, products, materials, days)
  * per-endpoint latency: min / mean / median / p95 / max, versus the 500 ms budget
  * forecast accuracy (MAPE) plus the diagnostics needed to defend that number

Everything is printed as paste-ready Markdown tables.

Run it inside the backend container, which already has the dependencies and can
reach both the API and the database:

    # measure whatever is currently loaded
    docker-compose exec backend python scripts/benchmark_nfr.py

    # load your own CSVs first, then measure
    docker-compose exec backend python scripts/benchmark_nfr.py \\
        --import-dir data/project --reset

    # check which files would be picked up, without touching the database
    docker-compose exec backend python scripts/benchmark_nfr.py \\
        --import-dir data/project --dry-run

CSV files are matched by filename, ignoring any ``_template`` / ``_data`` /
``_export`` / ``_import`` / ``_sample`` suffix, and are always imported in
dependency order regardless of the order you list them.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

API = "http://localhost:8000"
BUDGET_MS = 500.0

# Import endpoints in dependency order: a recipe needs its product, an order
# line needs its recipe. Same order the dashboard's bulk upload enforces.
IMPORT_ORDER: list[tuple[str, str]] = [
    ("raw_materials", "/api/v1/import/raw_materials"),
    ("raw_material_inventory", "/api/v1/import/raw_material_inventory"),
    ("products", "/api/v1/import/products"),
    ("final_products", "/api/v1/import/products"),
    ("recipes", "/api/v1/import/recipes"),
    ("recipe_items", "/api/v1/import/recipe_items"),
    ("orders", "/api/v1/import/orders"),
    ("order_items", "/api/v1/import/order_items"),
    ("transactions", "/api/v1/import/transactions"),
]

# Endpoints measured with the full sample count. Cheap, SQL-backed.
ANALYTICAL: list[tuple[str, str]] = [
    ("GET /health", "/health"),
    ("GET /products?limit=100", "/api/v1/products?limit=100"),
    ("GET /metrics/kpi", "/api/v1/metrics/kpi"),
    ("GET /metrics/cost-summary", "/api/v1/metrics/cost-summary"),
    ("GET /metrics/profitability", "/api/v1/metrics/profitability"),
    ("GET /metrics/customer-segments", "/api/v1/metrics/customer-segments"),
    ("GET /metrics/revenue-trend", "/api/v1/metrics/revenue-trend?days=180"),
    ("GET /inventory/status", "/api/v1/inventory/status"),
    ("GET /recommendations?limit=20", "/api/v1/recommendations?limit=20"),
]

# Endpoints measured with fewer samples: each request refits ARIMA models.
FORECASTS: list[tuple[str, str]] = [
    ("GET /forecasts/revenue?weeks_ahead=4", "/api/v1/forecasts/revenue?weeks_ahead=4"),
    ("GET /forecasts/revenue?weeks_ahead=12", "/api/v1/forecasts/revenue?weeks_ahead=12"),
]

_SUFFIXES = ("_template", "_data", "_export", "_import", "_sample")


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------

def _stem(filename: str) -> str:
    """Normalise a filename to its table key ('Orders_export.csv' -> 'orders')."""
    stem = filename.lower().rsplit(".", 1)[0].replace("-", "_").replace(" ", "_")
    for suffix in _SUFFIXES:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def match_files(directory: Path) -> tuple[list[tuple[str, str, Path]], list[Path]]:
    """Match CSVs in a directory to import endpoints, in dependency order.

    Returns:
        (matched, unrecognised) where matched is a list of
        (table key, endpoint path, file) tuples in the order they must be sent.
    """
    files = sorted(p for p in directory.iterdir() if p.suffix.lower() == ".csv")
    by_key: dict[str, Path] = {}
    unrecognised: list[Path] = []

    known = {key for key, _ in IMPORT_ORDER}
    for path in files:
        stem = _stem(path.name)
        hit = next(
            (k for k in known if stem == k or stem.startswith(f"{k}_") or stem.endswith(f"_{k}")),
            None,
        )
        if hit is None:
            unrecognised.append(path)
        elif hit not in by_key:
            by_key[hit] = path

    matched = [(key, ep, by_key[key]) for key, ep in IMPORT_ORDER if key in by_key]
    return matched, unrecognised


def run_import(client: httpx.Client, directory: Path, reset: bool, dry_run: bool) -> None:
    """Clear the database if asked, then POST each CSV to its import endpoint."""
    matched, unrecognised = match_files(directory)

    print(f"### CSV files in `{directory}`\n")
    if not matched:
        print("No recognised CSV files. Expected names (any prefix/suffix is stripped):")
        print("  " + " · ".join(f"`{k}.csv`" for k, _ in IMPORT_ORDER if k != "final_products"))
        sys.exit(1)

    for i, (key, _, path) in enumerate(matched, 1):
        size_kb = path.stat().st_size / 1024
        print(f"{i}. `{path.name}` -> **{key}** ({size_kb:,.0f} KB)")
    for path in unrecognised:
        print(f"-  `{path.name}` -> not recognised, will be skipped")
    print()

    if dry_run:
        print("_Dry run: nothing was sent._\n")
        return

    if reset:
        print("Clearing existing data ...")
        resp = client.post("/api/v1/import/clear", params={"confirm": True}, timeout=120.0)
        resp.raise_for_status()
        print(f"  deleted: {resp.json().get('deleted')}\n")

    print("| # | File | Endpoint | Result | Time |")
    print("|---|---|---|---|---|")
    for i, (key, endpoint, path) in enumerate(matched, 1):
        started = time.perf_counter()
        with path.open("rb") as handle:
            resp = client.post(
                endpoint,
                files={"file": (path.name, handle, "text/csv")},
                timeout=3600.0,
            )
        elapsed = time.perf_counter() - started

        if resp.status_code >= 400:
            summary = f"**HTTP {resp.status_code}** {resp.text[:120]}"
        else:
            body = resp.json()
            counts = {
                k: v for k, v in body.items()
                if k != "errors" and isinstance(v, int)
            }
            summary = ", ".join(f"{k}={v:,}" for k, v in counts.items())
            errors = body.get("errors") or []
            if errors:
                summary += f" — {len(errors)} error(s), first: {errors[0][:80]}"
        print(f"| {i} | `{path.name}` | `{key}` | {summary} | {elapsed:,.1f}s |")
    print()


# ---------------------------------------------------------------------------
# Dataset shape
# ---------------------------------------------------------------------------

def dataset_shape() -> dict:
    """Read the size and span of the loaded dataset straight from the database."""
    from sqlalchemy import func

    from backend.db.database import SessionLocal
    from backend.models.customer import Customer
    from backend.models.final_product import FinalProduct
    from backend.models.order import Order, OrderItem
    from backend.models.raw_material import RawMaterial
    from backend.models.recipe import Recipe, RecipeItem

    db = SessionLocal()
    try:
        first, last = db.query(func.min(Order.order_date), func.max(Order.order_date)).one()
        span = (last.date() - first.date()).days + 1 if first and last else 0
        return {
            "orders": db.query(Order).count(),
            "order_lines": db.query(OrderItem).count(),
            "products": db.query(FinalProduct).count(),
            "materials": db.query(RawMaterial).count(),
            "recipes": db.query(Recipe).count(),
            "recipe_items": db.query(RecipeItem).count(),
            "customers": db.query(Customer).count(),
            "days": span,
            "first_order": first.date().isoformat() if first else None,
            "last_order": last.date().isoformat() if last else None,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Latency
# ---------------------------------------------------------------------------

def measure(client: httpx.Client, path: str, samples: int, warmup: int = 3) -> Optional[dict]:
    """Time `samples` GET requests, discarding `warmup` calls first.

    Returns:
        Latency statistics in milliseconds, or None if the endpoint errored.
    """
    for _ in range(warmup):
        try:
            client.get(path, timeout=300.0)
        except httpx.HTTPError:
            return None

    timings: list[float] = []
    status = 200
    for _ in range(samples):
        started = time.perf_counter()
        try:
            resp = client.get(path, timeout=300.0)
        except httpx.HTTPError as exc:
            return {"error": type(exc).__name__}
        timings.append((time.perf_counter() - started) * 1000)
        status = resp.status_code

    if status >= 400:
        return {"error": f"HTTP {status}"}

    timings.sort()
    p95_index = min(len(timings) - 1, int(len(timings) * 0.95))
    return {
        "min": timings[0],
        "mean": statistics.fmean(timings),
        "median": statistics.median(timings),
        "p95": timings[p95_index],
        "max": timings[-1],
        "n": len(timings),
    }


def latency_table(client: httpx.Client, endpoints: list[tuple[str, str]], samples: int) -> None:
    """Print one Markdown latency table for a group of endpoints."""
    print(f"| Endpoint | n | min | mean | median | p95 | max | < {BUDGET_MS:.0f} ms |")
    print("|---|---:|---:|---:|---:|---:|---:|:--:|")
    for name, path in endpoints:
        stats = measure(client, path, samples)
        if stats is None or "error" in stats:
            reason = (stats or {}).get("error", "unreachable")
            print(f"| `{name}` | — | — | — | — | — | — | {reason} |")
            continue
        verdict = "yes" if stats["p95"] < BUDGET_MS else "**NO**"
        print(
            f"| `{name}` | {stats['n']} "
            f"| {stats['min']:.1f} | {stats['mean']:.1f} | {stats['median']:.1f} "
            f"| {stats['p95']:.1f} | {stats['max']:.1f} | {verdict} |"
        )
    print()
    print("_Latency in milliseconds, wall-clock round trip. "
          f"{samples} samples per endpoint after 3 discarded warm-up calls._\n")


# ---------------------------------------------------------------------------
# Forecast accuracy
# ---------------------------------------------------------------------------

def forecast_diagnostics() -> None:
    """Report MAPE alongside the diagnostics that explain it.

    MAPE depends on the dataset's daily volatility, not only on the model. This
    prints the coefficient of variation, the score a constant-mean forecast
    would achieve, and the weekday profile, so the number can be defended.
    """
    import pandas as pd
    from sqlalchemy import func

    from backend.db.database import SessionLocal
    from backend.models.order import Order
    from models.forecasting.demand_forecast import DemandForecaster

    db = SessionLocal()
    try:
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
    finally:
        db.close()

    if len(rows) < 14:
        print(f"Only {len(rows)} day(s) of order history — forecasting needs at least 14.\n")
        return

    frame = pd.DataFrame([{"ds": str(r.ds), "y": float(r.y or 0)} for r in rows])
    n = len(frame)
    holdout = max(7, int(n * 0.2))

    mean_daily = frame.y.mean()
    cv = frame.y.std() / mean_daily if mean_daily else 0.0
    # A constant forecast at the series mean scores this MAPE. If the model does
    # not beat it, the model is not capturing structure.
    baseline = (frame.y - mean_daily).abs().mean() / mean_daily if mean_daily else 0.0

    forecaster = DemandForecaster().fit(frame)
    predicted = pd.DataFrame(forecaster.predict(periods=28)).forecast
    pred_cv = predicted.std() / predicted.mean() if predicted.mean() else 0.0

    print("| Measure | Value |")
    print("|---|---:|")
    print(f"| Days of history | {n} |")
    print(f"| Holdout used for MAPE | {holdout} days (last 20%, single multi-step forecast) |")
    print(f"| Selected ARIMA order | {forecaster._forecaster.order} |")
    print(f"| **MAPE** | **{forecaster.mape * 100:.2f}%** |")
    print(f"| MAPE of a constant-mean forecast | {baseline * 100:.2f}% |")
    print(f"| Mean daily revenue | {mean_daily:,.1f} |")
    print(f"| CV of actual daily revenue | {cv:.3f} |")
    print(f"| CV of the 28-day forecast | {pred_cv:.3f} |")
    print()

    if forecaster.mape >= baseline:
        print("> The model does **not** beat a constant at the series mean. Its forecast is")
        print("> effectively flat, so MAPE is measuring the data's daily volatility rather")
        print("> than the model's skill.\n")

    weekday = frame.assign(dow=pd.to_datetime(frame.ds).dt.dayofweek).groupby("dow").y.mean()
    if len(weekday) == 7:
        lift = weekday[5:].mean() / weekday[:5].mean()
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        print("| " + " | ".join(names) + " | weekend lift |")
        print("|" + "---:|" * 8)
        print("| " + " | ".join(f"{v:,.0f}" for v in weekday) + f" | {lift:.2f}x |")
        print()
        if lift > 1.15 or lift < 0.87:
            print("> A weekly cycle this strong is not modelled: `ARIMAForecaster.DEFAULT_ORDERS`")
            print("> holds only non-seasonal orders. `SARIMAX` is imported in")
            print("> `models/forecasting/time_series.py` but never called.\n")


# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure VendorIO API latency and forecast accuracy on one dataset."
    )
    parser.add_argument("--import-dir", type=Path, help="directory of CSVs to import first")
    parser.add_argument("--reset", action="store_true", help="delete all data before importing")
    parser.add_argument("--dry-run", action="store_true", help="list matched files, import nothing")
    parser.add_argument("--samples", type=int, default=25, help="samples per endpoint (default 25)")
    parser.add_argument(
        "--forecast-samples", type=int, default=7, help="samples per forecast endpoint (default 7)"
    )
    args = parser.parse_args()

    client = httpx.Client(base_url=API)

    try:
        client.get("/health", timeout=10.0).raise_for_status()
    except httpx.HTTPError as exc:
        print(f"Cannot reach the API at {API}: {exc}", file=sys.stderr)
        print("Run this inside the backend container:", file=sys.stderr)
        print("  docker-compose exec backend python scripts/benchmark_nfr.py", file=sys.stderr)
        sys.exit(1)

    print("# VendorIO — NFR measurement\n")
    print(f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}._\n")

    if args.import_dir:
        if not args.import_dir.is_dir():
            print(f"Not a directory: {args.import_dir}", file=sys.stderr)
            sys.exit(1)
        print("## 1. Data import\n")
        run_import(client, args.import_dir, args.reset, args.dry_run)
        if args.dry_run:
            return

    print("## 2. Dataset measured\n")
    shape = dataset_shape()
    print("| Property | Value |")
    print("|---|---:|")
    for label, key in [
        ("Orders", "orders"),
        ("Order lines", "order_lines"),
        ("Products", "products"),
        ("Raw materials", "materials"),
        ("Recipes", "recipes"),
        ("Recipe items", "recipe_items"),
        ("Customers", "customers"),
        ("Days covered", "days"),
    ]:
        print(f"| {label} | {shape[key]:,} |")
    if shape["first_order"]:
        print(f"| Date range | {shape['first_order']} to {shape['last_order']} |")
        if shape["days"]:
            print(f"| Mean orders/day | {shape['orders'] / shape['days']:,.1f} |")
    print()

    print("## 3. Latency — NFR1 (response time under 500 ms)\n")
    print("### SQL-backed analytical endpoints\n")
    latency_table(client, ANALYTICAL, args.samples)
    print("### Forecast endpoints (refit ARIMA on every request)\n")
    latency_table(client, FORECASTS, args.forecast_samples)

    print("## 4. Forecast accuracy — NFR2 (MAPE under 10%)\n")
    forecast_diagnostics()

    print("---\n")
    print("**Caveats to state in the report.** The API runs under Uvicorn in development")
    print("mode (`--reload`, single worker) as configured in `docker-compose.yml`; a")
    print("production run would differ. Latency is measured from inside the container, so")
    print("it excludes network transit. MAPE is a property of this dataset as much as of")
    print("the model — quote it with the dataset shape from section 2.")


if __name__ == "__main__":
    main()
