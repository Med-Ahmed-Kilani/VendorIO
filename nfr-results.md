# VendorIO — NFR measurement

_Generated 2026-09-09 13:08:41._

## 1. Data import

### CSV files in `data/project`

1. `raw_materials.csv` -> **raw_materials** (1 KB)
2. `raw_material_inventory.csv` -> **raw_material_inventory** (2 KB)
3. `final_products.csv` -> **products** (1 KB)
4. `recipes.csv` -> **recipes** (1 KB)
5. `recipe_items.csv` -> **recipe_items** (3 KB)
6. `orders.csv` -> **orders** (1,186 KB)
7. `order_items.csv` -> **order_items** (1,102 KB)
8. `transactions.csv` -> **transactions** (1,005 KB)

Clearing existing data ...
  deleted: {'transactions': 15596, 'order_items': 29075, 'orders': 21248, 'customers': 1064, 'recipe_items': 88, 'recipes': 46, 'final_products': 39, 'raw_material_inventory': 37, 'raw_materials': 37}

| # | File | Endpoint | Result | Time |
|---|---|---|---|---|
| 1 | `raw_materials.csv` | `raw_materials` | created=29, updated=0, skipped=0 | 0.1s |
| 2 | `raw_material_inventory.csv` | `raw_material_inventory` | updated=29, skipped=0 | 0.0s |
| 3 | `final_products.csv` | `products` | created=33, updated=0, skipped=0 | 0.0s |
| 4 | `recipes.csv` | `recipes` | created=39, updated=0, skipped=0 | 0.0s |
| 5 | `recipe_items.csv` | `recipe_items` | created=78, updated=0, skipped=0 | 0.1s |
| 6 | `orders.csv` | `orders` | orders_created=15,596, items_created=0, skipped=0 | 8.2s |
| 7 | `order_items.csv` | `order_items` | created=20,662, skipped=0 | 3.9s |
| 8 | `transactions.csv` | `transactions` | created=15,596, skipped=0 | 16.0s |

## 2. Dataset measured

| Property | Value |
|---|---:|
| Orders | 15,596 |
| Order lines | 20,662 |
| Products | 33 |
| Raw materials | 29 |
| Recipes | 39 |
| Recipe items | 78 |
| Customers | 999 |
| Days covered | 90 |
| Date range | 2026-02-14 to 2026-05-14 |
| Mean orders/day | 173.3 |

## 3. Latency — NFR1 (response time under 500 ms)

### SQL-backed analytical endpoints

| Endpoint | n | min | mean | median | p95 | max | < 500 ms |
|---|---:|---:|---:|---:|---:|---:|:--:|
| `GET /health` | 25 | 0.7 | 1.2 | 0.9 | 2.8 | 4.0 | yes |
| `GET /products?limit=100` | 25 | 1.2 | 1.7 | 1.7 | 2.3 | 2.5 | yes |
| `GET /metrics/kpi` | 25 | 3.4 | 4.5 | 4.2 | 5.8 | 9.0 | yes |
| `GET /metrics/cost-summary` | 25 | 7.7 | 8.8 | 8.5 | 10.3 | 12.5 | yes |
| `GET /metrics/profitability` | 25 | 5.5 | 6.2 | 6.2 | 6.5 | 7.9 | yes |
| `GET /metrics/customer-segments` | 25 | 8.4 | 12.8 | 9.1 | 51.8 | 55.1 | yes |
| `GET /metrics/revenue-trend` | 25 | 3.6 | 4.0 | 3.9 | 4.7 | 4.8 | yes |
| `GET /inventory/status` | 25 | 84.3 | 109.8 | 96.6 | 123.8 | 367.6 | yes |
| `GET /recommendations?limit=20` | 25 | 72.6 | 104.8 | 97.3 | 226.7 | 237.4 | yes |

_Latency in milliseconds, wall-clock round trip. 25 samples per endpoint after 3 discarded warm-up calls._

### Forecast endpoints (refit ARIMA on every request)

| Endpoint | n | min | mean | median | p95 | max | < 500 ms |
|---|---:|---:|---:|---:|---:|---:|:--:|
| `GET /forecasts/revenue?weeks_ahead=4` | 7 | 264.0 | 303.8 | 285.0 | 356.9 | 356.9 | yes |
| `GET /forecasts/revenue?weeks_ahead=12` | 7 | 289.2 | 335.2 | 308.5 | 472.4 | 472.4 | yes |

_Latency in milliseconds, wall-clock round trip. 7 samples per endpoint after 3 discarded warm-up calls._

## 4. Forecast accuracy — NFR2 (MAPE under 10%)

| Measure | Value |
|---|---:|
| Days of history | 90 |
| Holdout used for MAPE | 18 days (last 20%, single multi-step forecast) |
| Selected ARIMA order | (1, 1, 1) |
| **MAPE** | **10.07%** |
| MAPE of a constant-mean forecast | 10.68% |
| Mean daily revenue | 1,318.7 |
| CV of actual daily revenue | 0.129 |
| CV of the 28-day forecast | 0.004 |

| Mon | Tue | Wed | Thu | Fri | Sat | Sun | weekend lift |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,260 | 1,263 | 1,238 | 1,205 | 1,256 | 1,516 | 1,488 | 1.21x |

> A weekly cycle this strong is not modelled: `ARIMAForecaster.DEFAULT_ORDERS`
> holds only non-seasonal orders. `SARIMAX` is imported in
> `models/forecasting/time_series.py` but never called.

---

**Caveats to state in the report.** The API runs under Uvicorn in development
mode (`--reload`, single worker) as configured in `docker-compose.yml`; a
production run would differ. Latency is measured from inside the container, so
it excludes network transit. MAPE is a property of this dataset as much as of
the model — quote it with the dataset shape from section 2.
