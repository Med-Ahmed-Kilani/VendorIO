# VendorIO — Technical Dossier

**For:** 2nd-year internship report, Data Science Engineering
**Source:** repository audit, branch `main`, commit `9b4f74c`
**Date:** 9 September 2026

| | |
|---|---|
| Lines of Python | 6,449 |
| Source files | 103 |
| Database tables | 9 |
| REST endpoints | 34 |
| Test functions | 76 |
| Commits | 5 (Apr → Jun 2026) |

---

## Contents

1. [Project identity](#1-project-identity)
2. [Problem statement and target user](#2-problem-statement-and-target-user)
3. [The pivot: from product to bill of materials](#3-the-pivot-from-product-to-bill-of-materials)
4. [Architecture](#4-architecture)
5. [Data model](#5-data-model)
6. [The ingestion pipeline](#6-the-ingestion-pipeline)
7. [The analytics engine](#7-the-analytics-engine)
8. [The dashboard](#8-the-dashboard)
9. [Technology stack and justification](#9-technology-stack-and-justification)
10. [Quality, testing and engineering practice](#10-quality-testing-and-engineering-practice)
11. [Project metrics](#11-project-metrics)
12. [Limitations and future work](#12-limitations-and-future-work)
13. [Report structure](#13-report-structure)
14. [Figures to produce](#14-figures-to-produce)
15. [Glossary](#15-glossary)

---

## 1. Project identity

VendorIO is a decision-support web platform that turns a small business's sales history into three concrete answers: **what to reorder and when**, **what each product actually costs**, and **how much will sell over the next four weeks**.

| Field | Value |
|---|---|
| Name | VendorIO (v0.1.0) |
| Type | Monorepo — 3-tier web application |
| Domain | Supply chain & business intelligence |
| Target sector | Food service & artisanal production |
| Deployment | Single-tenant, self-hosted (Docker) |
| Access control | None — no authentication (MVP) |
| Language | Python 3.11 (100%) |
| Database | PostgreSQL 15 |
| Period | 24 April → 15 June 2026 |
| Status | Working MVP, not deployed to production |

### The value proposition in one sentence

A café owner drops in their CSV exports; within minutes they get a prioritised reorder list, the real margin on every drink broken down ingredient by ingredient, and a four-week revenue forecast — with no ERP, no subscription, and without leaving their spreadsheets behind.

---

## 2. Problem statement and target user

### The business problem

A small production business lives with a permanent contradiction: it **sells finished products** (a flat white, a croissant) but it **buys and stocks raw materials** (coffee beans, milk, flour). Between the two sits a recipe. As a result:

- The owner cannot say how many *days of trading* the remaining coffee represents — they see a sack, not a deadline.
- **Stockouts** are discovered on the morning they happen, which halts production.
- Cash is tied up in slow-moving ingredients with no measurement of the **holding cost**.
- The selling price is known; the **true cost of goods** per portion size rarely is.
- Purchasing is done by instinct, with no **economic order quantity** and no **reorder point**.

### Review of existing solutions

| Category | Examples | Limitation for a small business |
|---|---|---|
| Spreadsheet | Excel, Google Sheets | No forecasting, no turnover calculation, manual errors, no bill of materials |
| ERP / WMS | SAP Business One, Odoo Inventory | Cost and integration complexity out of all proportion; months-long rollout |
| Point of sale | Square, Lightspeed | *Sales* analytics, not *stock* optimisation; no recipe model |
| Generic BI | Power BI, Metabase | Visualises but does not decide: no EOQ, no alerting, no rules engine |

**VendorIO's niche:** the decision layer missing between the spreadsheet and the ERP — simple enough to be fed by CSV files, equipped enough to produce quantified recommendations.

### Actors

| Actor | Role | Primary use cases |
|---|---|---|
| **Owner-manager** *(primary)* | Runs the business | Import data · Review KPIs · Review alerts · Export reorder list · Analyse margins |
| **Purchasing officer** | Places supplier orders | Check stock levels · Download the reorder list · Track lead times |
| **Point-of-sale system** *(secondary)* | Data source | Supplies CSV exports of orders (manual integration in the MVP) |

> **Reference persona to cite in the report**
>
> An independent café with 5 to 50 SKUs, 10 to 200 orders a day, no information system, whose stock accounting lives in a notebook or a spreadsheet, and whose owner has neither the time nor the training to operate an ERP. This persona justifies every technical decision in the project: CSV import, single tenancy, and one-command Docker deployment.

---

## 3. The pivot: from product to bill of materials

This is **the narrative core of the report**. The project was designed around a conventional e-commerce model, then entirely re-modelled six weeks in, once that model proved wrong for the real target user.

### v1 — the "product" model
*PRD of 24 April 2026 · abandoned*

**Assumption**

- You **sell what you stock**: a single `products` table carries selling price, unit cost and stock level at once.
- 5 tables: `products`, `orders`, `order_items`, `customers`, `inventory_snapshots`.
- Cost of goods is a `cost_per_unit` column.
- Consumption equals units sold.

**Why it breaks**

- A café does not stock "flat whites". It stocks milk and beans.
- No way to model sizes (S/M/L), which consume different quantities.
- No way to answer "I have three days of milk left".

### v2 — the "recipe" model
*Migration of 15 June 2026 · current*

**Principle**

- Strict separation: `final_products` (what you sell, carries the **price**) versus `raw_materials` (what you stock, carries the **cost**, lead time and reorder point).
- Between them, a **bill of materials**: `recipes` (product × size) and `recipe_items` (recipe → material, quantity).
- Stock moves from the product to the material (`raw_material_inventory`).
- Consumption is **derived, never entered**: it is computed by "exploding" each order line through its recipe.

**What this unlocks**

- Days to stockout *per ingredient*.
- True margin per product and per size.
- EOQ and reorder point on what is actually purchased.

### How the migration was carried out

The Alembic migration `001_recipe_schema` (306 lines) is worth documenting in detail: it does not merely create tables, it **carries the existing data across**. Every legacy product becomes simultaneously a finished product *and* a 1:1 raw material, with a default single-ingredient recipe — so no history is lost and the user can refine their real recipes by CSV afterwards.

- Creation of the 6 new tables and their indexes.
- `INSERT … SELECT` from `products` into `final_products` and then `raw_materials`, with `setval()` to resynchronise the identity sequences.
- Generation of one default recipe per product (`size = NULL`) plus a `recipe_item` at quantity 1.
- Addition of `size`, `recipe_id` and `unit_cost` to `order_items`, then **backfilling** of the historical cost.
- Foreign keys switched from `products` to `final_products`, using `DO $$ … $$` blocks that handle both possible constraint names depending on whether the database was created by SQLAlchemy or by the seed SQL script.
- Removal of the legacy tables.

> **Engineering decision worth highlighting**
>
> The migration is **deliberately irreversible**: `downgrade()` raises `NotImplementedError` with the message "restore from backup". This is a stated choice rather than an oversight — since the legacy table is dropped, an automatic downgrade would give a false sense of safety.

---

## 4. Architecture

A conventional 3-tier architecture, organised as a **monorepo** of four independent Python packages declared in `pyproject.toml`. The presentation tier talks to the business tier over HTTP/JSON and never touches the database directly, which makes the dashboard replaceable.

```
┌──────────────────────────────────────────────────────────────┐
│  PRESENTATION — dashboard/ (1,746 lines)                     │
│  Streamlit · 6 pages · reusable components (KPI cards,       │
│  Plotly charts, tables) · httpx client · 5-min TTL cache     │
└───────────────────────────┬──────────────────────────────────┘
                            │  HTTP / JSON
┌───────────────────────────▼──────────────────────────────────┐
│  APPLICATION — backend/ (3,206 lines)                        │
│  FastAPI · 8 routers, 34 endpoints · logging middleware      │
│  (request ID + response time) · global exception handler     │
│  · auto-generated OpenAPI                                    │
└───────────────────────────┬──────────────────────────────────┘
                            │  Python calls
┌───────────────────────────▼──────────────────────────────────┐
│  BUSINESS & MODELS — backend/services/ + models/             │
│  Services (KPIs, inventory, costs, recommendations) ·        │
│  models/ package: ARIMA forecasting, optimisation, RFM       │
└───────────────────────────┬──────────────────────────────────┘
                            │  SQLAlchemy 2.0 ORM
┌───────────────────────────▼──────────────────────────────────┐
│  PERSISTENCE — PostgreSQL 15                                 │
│  9 tables · JSONB for flexible attributes · versioned        │
│  Alembic migrations · pool (10 + 20 overflow, pre-ping)      │
└──────────────────────────────────────────────────────────────┘
```

### Backend layering

| Layer | Path | Responsibility |
|---|---|---|
| Routes | `backend/api/v1/` | HTTP contract, parameter validation, error codes |
| Schemas | `backend/schemas/` | Pydantic request/response contracts, business validation (price ≥ 0) |
| Services | `backend/services/` | Business logic: KPIs, inventory health, costing, rules engine |
| CRUD | `backend/crud/` | Typed generic data access (`CRUDBase`) plus specific queries |
| ORM | `backend/models/` | Table definitions, relationships, constraints |
| Injection | `backend/dependencies.py` | Per-request database session via `Depends(get_db)`, guaranteed close |

> **Point to defend in the viva**
>
> FastAPI's dependency injection makes it possible to **substitute the database in tests**: the test suite overrides `get_db` with an in-memory SQLite session (`StaticPool`), giving fast API tests that need no container. This is exactly the kind of decision an examiner expects you to be able to justify.

---

## 5. Data model

Nine tables across three domains.

### Supply — what the business buys and stocks

**`raw_materials`**
`id` (PK) · `name` (unique) · `external_id` ("MAT-001") · `category` · `unit` (g/ml/pcs) · `cost_per_unit` · `reorder_point` · `lead_time_days`

**`raw_material_inventory`**
`id` (PK) · `material_id` (FK) · `current_stock` · `created_at` / `updated_at`

### Bill of materials — the bridge between buying and selling

**`final_products`**
`id` (PK) · `name` (unique) · `external_id` · `category` · `unit_price`

**`recipes`**
`id` (PK) · `product_id` (FK) · `external_id` ("RCP-001") · `size` (S/M/L/NULL) · `unit_cost` NUM(10,4)

**`recipe_items`**
`id` (PK) · `recipe_id` (FK) · `material_id` (FK) · `quantity_needed` · `unit` · `notes`

### Sales — what goes out, and what gets paid

**`customers`**
`id` (PK) · `email` · `first_order_date` · `total_spent` · `order_count` · `customer_attributes` (JSONB)

**`orders`**
`id` (PK) · `order_date` · `customer_id` (FK) · `total_amount` · `status` · `metadata` (JSONB)

**`order_items`**
`id` (PK) · `order_id` (FK) · `product_id` (FK) · `recipe_id` (FK) · `size` · `quantity` · `unit_price` · `unit_cost` · `line_total`

**`transactions`**
`id` (PK) · `order_id` (FK) · `amount_paid` · `payment_method`

### Relationships and cardinalities

*Transfer directly into the class diagram.*

| Parent | Card. | Child | Meaning |
|---|---|---|---|
| `customers` | 1 — N | `orders` | A customer places many orders |
| `orders` | 1 — N | `order_items` | Order composition (cascade delete) |
| `orders` | 1 — N | `transactions` | Payments, possibly split |
| `final_products` | 1 — N | `recipes` | One recipe per portion size |
| `recipes` | 1 — N | `recipe_items` | **The bill of materials** — ingredients and quantities |
| `raw_materials` | 1 — N | `recipe_items` | One material is used in many recipes |
| `raw_materials` | 1 — 1 | `raw_material_inventory` | Current stock level (latest row wins) |
| `recipes` | 1 — N | `order_items` | Trace of the cost frozen at the time of sale |

### Two modelling decisions worth explaining

> **1 — The cost snapshot**
>
> `order_items.unit_cost` is **copied from the recipe at import time** and never changes afterwards. If the price of coffee doubles in March, the margin computed on January's sales stays correct. This is the principle of point-in-time correctness: cost of goods sold must never be recalculated retroactively from today's prices. Every COGS calculation reads this frozen column, not the live recipe.

> **2 — The uniqueness constraint on size**
>
> `UNIQUE(order_id, product_id, size)`: one order can contain a small latte *and* a large latte — two distinct lines with two different costs. The v1 constraint `UNIQUE(order_id, product_id)` forbade this. It is a concrete example of an integrity constraint dictated by the business domain, worth citing in the design chapter.

**Note for writing:** two files are still inherited from v1 — `backend/models/product.py` and `backend/models/inventory.py`. Their tables are dropped by the migration; the classes are no longer exported and are dead code. Do not include them in the class diagram.

---

## 6. The ingestion pipeline

This is the largest module in the project (**1,029 lines**, `backend/api/v1/import_data.py`) and, for a data engineering report, the richest to describe: nine import endpoints, a strict dependency order, and a tolerant identifier-resolution chain.

### The dependency order

You cannot import an order before its recipe, nor a recipe before its product. The dashboard therefore enforces the order automatically:

| # | Endpoint | Purpose |
|---|---|---|
| 01 | `raw_materials` | Raw materials and their purchasing characteristics (cost, lead time, reorder point). Also creates the initial inventory row. |
| 02 | `raw_material_inventory` | Stock-level updates without touching the material master records. |
| 03 | `products` | The finished products sold and their selling price. |
| 04 | `recipes` | One row per product × size pair, carrying the unit cost of goods. |
| 05 | `recipe_items` | The detailed bill of materials: which material, in what quantity, in which recipe. |
| 06 | `orders` | Order headers, or a "flat" line-by-line format (detected automatically). |
| 07 | `order_items` | Order lines attached to orders already present in the database. |
| 08 | `transactions` | Payments received and payment methods. |
| 09 | `/import/clear` | Full purge, in reverse dependency order, guarded by `confirm=true`. |

### Notable mechanisms

**Cascading identifier resolution.** A real CSV never contains the database's internal identifiers. Every reference is therefore resolved by trying, in order: the **numeric id**, then the **external identifier** such as `MAT-001` or `RCP-001` (the `external_id` columns added by migrations 002 and 003), then the **exact name**. This is what lets an owner keep using their own codes.

**Automatic order-format detection.** The `/import/orders` endpoint inspects the columns: if `product_id` and `quantity` are present it switches to "flat" mode and groups rows into orders (by `order_id`, or failing that by date + email); otherwise it treats the file as headers only. One endpoint, two real-world formats.

**Hard rejection of lines with no recipe.** An order line whose product has no recipe for the requested size is **refused**, with a message naming the row number and the corrective action — otherwise the cost calculation would be silently wrong. In flat mode, if a single line in a group fails, **the entire order is discarded** (`db.expunge`): no partially loaded orders.

**N+1 query optimisation.** The order-line importer preloads every order, product and recipe into in-memory dictionaries before the loop, instead of querying the database per row. For 10,000 rows this goes from tens of thousands of queries to three. It is a concrete, measurable performance point worth putting forward.

**Guided import interface.** On the dashboard side (`0_import.py`, 776 lines):

- **Bulk drop**: all files at once, recognised by filename (the suffixes `_template`, `_data`, `_export` are stripped) and imported in the correct order.
- **Column mapping**: every expected field has an alias dictionary (`price`, `sale_price`, `selling_price` → `unit_price`). Auto-detection proposes; the user corrects with a dropdown.
- **Downloadable templates** for each of the eight files, pre-filled with a coherent café example.
- **Before/after preview** of the mapping on the first five rows.
- **Import report**: created / updated / skipped, with the first 20 errors located by row number.
- **Navigation gating**: while no data exists, only the import page is visible.

---

## 7. The analytics engine

### The founding calculation: bill-of-materials explosion

Everything else follows from it. Stock is never decremented by sales; consumption is **reconstructed** from order history by traversing the recipes:

```
D̄(material) = Σ (order_item.quantity × recipe_item.quantity_needed) ÷ 90
```

Summed over every order line of the last 90 days whose recipe contains the material. The window is anchored on **the most recent order date in the database**, not on today — which makes the analysis reproducible on a historical dataset.

*Source: `backend/services/inventory_service.py · _material_daily_consumption()`*

### Inventory management indicators

| Indicator | Formula | Notes |
|---|---|---|
| **Reorder point** (ROP) | `ROP = D̄ × L` | L = supplier lead time in days (7 by default). A manually entered threshold overrides the computed one. |
| **Economic order quantity** (EOQ) | `Q* = √(2·D·S / H)` | D = annual demand, S = ordering cost (25.00, configurable), H = annual holding cost per unit = cost × 25%. Known in French as the *formule de Wilson*. |
| **Days to stockout** (DTS) | `DTS = stock ÷ D̄` | Drives status: < 7 d critical, < 14 d warning, otherwise ok. |
| **Inventory turnover** | `T = (D̄ × 365) ÷ stock` | Classified by quartile: ≤ P25 "slow", ≥ P75 "fast", otherwise "average". |
| **Holding cost** (monthly) | `Hm = cost × stock × 0.25 ÷ 12` | An annual rate of 25% of the capital tied up, set by environment variable. |
| **Gross margin** | `M = (Revenue − COGS) ÷ Revenue` | COGS computed from frozen costs: `Σ(unit_cost × quantity)` over order lines. |

### Worked example to reproduce in the report

Arabica beans: cost 0.0095 per gram · stock 20,000 g · reorder point 5,000 g · lead time 7 days. A flat white uses 18 g; you sell 60 a day.

1. `D̄ = 60 × 18 = ` **1,080 g/day**
2. `DTS = 20,000 ÷ 1,080 = ` **18.5 days** → status **ok**
3. Computed `ROP = 1,080 × 7 = ` **7,560 g** *(but the entered threshold, 5,000 g, takes precedence)*
4. `Turnover = 1,080 × 365 ÷ 20,000 = ` **19.7 times/year**
5. `Hm = 0.0095 × 20,000 × 0.25 ÷ 12 = ` **3.96 per month**
6. Annual `D = 1,080 × 365 = 394,200 g` · `H = 0.0095 × 0.25 = 0.002375`
7. `Q* = √(2 × 394,200 × 25 ÷ 0.002375) ≈ ` **91,100 g ≈ 91 kg**

### Demand forecasting

| Aspect | Choice made | Justification |
|---|---|---|
| Model | ARIMA (statsmodels) | Chosen *against* the Prophet specified in the requirements: no C++ toolchain, light install, sufficient on short series |
| Order selection | Grid over (1,1,1), (2,1,1), (1,1,2), (2,1,2), AIC criterion | A compromise between full auto-ARIMA and a fixed order; four fits per request |
| Preparation | Re-indexed on a complete calendar, missing days filled with 0 | ARIMA requires a regular frequency; a day with no sales is real information |
| Validation | MAPE on the final 20% (minimum 7 days), refit on the training split | Avoids in-sample evaluation; the metric is exposed by the API and displayed in the UI |
| Uncertainty | 80% confidence interval (`alpha=0.2`) | Tighter than 95% and more actionable for a reorder decision |
| Guard rail | Minimum 14 days of history, otherwise an explicit HTTP 400 | Refusing a forecast is better than producing a wrong one |
| Outputs | Daily forecast plus weekly aggregation | Negative bounds clamped to 0: negative revenue is meaningless |

### The recommendation engine

A **rules-based** approach, deliberately non-probabilistic: every recommendation must be explainable to the owner in one sentence. Four rules, sorted by urgency.

| Rule | Condition | Urgency | Action produced |
|---|---|---|---|
| **Stockout risk** | DTS ≤ 14 days | critical if ≤ 7 d, else high | Recommend the EOQ quantity (floor: 2 × ROP) |
| **Slow mover** | Turnover ≤ P25 and stock > 0 | medium | Space out orders; quantifies the annual holding-cost saving |
| **Overstock** | DTS > 180 days | low | Reduce the next order; quantifies the cash freed up |
| **Bulk order** | Consumption in the top 10% and saving > 50 | low | Order the EOQ quantity to capture a 5% discount |

### Customer segmentation

Two implementations coexist — a point of honesty worth mentioning. The API serves a simple segmentation by order count (new / returning / loyal), while `models/analytics/segmentation.py` contains a full **RFM segmentation** (Recency, Frequency, Monetary) with quintile scoring and six segments (*champions*, *loyal*, *at risk*…), tested but **not wired into the API**. Excellent material for the future-work section.

---

## 8. The dashboard

| Page | Content | Interactions |
|---|---|---|
| **0 · Import** *(776 lines)* | Ten tabs: bulk drop, the 8 file types, data management. CSV templates, column mapping, detailed import reports. | Multi-file upload, mapping dropdowns, template downloads, guarded purge |
| **1 · Overview** | Seven KPIs (revenue, profit, orders, repeat rate, average order value, customers), revenue trend line, top 5 and bottom 5 products, customer segment table | Date-range picker, bottom-5 expander |
| **2 · Inventory** | Critical / warning / needs-reorder counters and total holding cost, inventory health table, turnover × days-remaining scatter, holding cost per material | Text search, status filter, **CSV export of the reorder list** |
| **3 · Costs** | Revenue / COGS / gross profit / margin rate, margin gauge, alert on products below 10% margin, COGS + holding versus revenue breakdown | Chart/table tabs, CSV export of the profitability report |
| **4 · Forecasts** | Revenue forecast with confidence band, MAPE and model displayed, per-product forecast, weekly summary | 1-to-12-week slider, product selector |
| **5 · Alerts** | Recommendations sorted by urgency, cumulative potential savings, contextual alert banner | Multi-select filters by urgency and type, action tracker |

### Presentation-tier implementation choices

- **TTL cache** of 5 minutes on every API call (`st.cache_data`) — avoids recomputing KPIs on every filter interaction.
- **Conditional navigation**: the five analytics pages appear only once the database holds data, which removes the confusing empty screen.
- **Graceful degradation**: the HTTP client distinguishes a server error from an unreachable backend, with a message tailored to each case.
- **Centralised colour semantics** in `dashboard/config.py`: statuses and urgencies share a single palette.
- **Plotly charts**: lines, bars, scatter plots, a gauge, and a confidence band built by stacking traces.

---

## 9. Technology stack and justification

The table below transposes directly into the "working environment" chapter. The right-hand column matters most: examiners penalise unjustified technology choices.

| Need | Technology | Version | Justification |
|---|---|---|---|
| Web API | **FastAPI** | 0.104 | Validation from type annotations, automatic OpenAPI documentation, native dependency injection, async performance |
| ASGI server | **Uvicorn** | 0.24 | The reference server for FastAPI, hot reload in development |
| ORM | **SQLAlchemy** | 2.0 | Typed `Mapped[]` API compatible with static checking, database independence (PostgreSQL in production, SQLite in tests) |
| Migrations | **Alembic** | 1.12 | Schema versioning, data migrations scriptable in raw SQL |
| Validation | **Pydantic** | 2.4 | Explicit input/output contracts, business validators, typed configuration from environment variables |
| Database | **PostgreSQL** | 15 | ACID compliance essential for financial data, JSONB for variable attributes without migration, efficient indexing |
| Time series | **statsmodels** | 0.14 | ARIMA with confidence intervals; preferred over Prophet to avoid the C++ build chain |
| ML metrics | **scikit-learn** | 1.3 | MAPE computation, validation utilities |
| Data handling | **pandas / numpy** | 2.1 / 1.26 | CSV reading and normalisation, aggregations, quantiles |
| User interface | **Streamlit** | 1.28 | A data interface in pure Python — no JavaScript context to maintain on an internship project |
| Visualisation | **Plotly** | 5.17 | Interactive charts, zoom and hover with no extra code |
| HTTP client | **httpx** | 0.25 | Modern API, timeout handling, also used by the test client |
| Dependencies | **Poetry** | 1.7 | Version locking (`poetry.lock`), reproducible builds, dev/prod groups |
| Testing | **pytest + pytest-cov** | 7.4 | Composable fixtures, coverage measurement |
| Code quality | **ruff + black** | 0.1 / 23.10 | Very fast linting (errors, imports, naming) and deterministic formatting at 100 columns |
| Containerisation | **Docker Compose** | 3.9 | Multi-stage build (base → backend / dashboard), PostgreSQL health check, dev/prod parity |
| Continuous integration | **GitHub Actions** | — | Two workflows (tests + lint), Poetry caching, coverage upload |
| Documentation | **MkDocs** | — | Markdown documentation, API reference generated from the OpenAPI schema |

---

## 10. Quality, testing and engineering practice

### Practices actually applied

- **Systematic type annotations** on function signatures, including return types.
- **Google-style docstrings** (Args / Returns / Example) throughout the `models/` package, with runnable examples.
- **Dedicated business exceptions** — `NotFoundError`, `ValidationError`, `ConflictError`, `InsufficientDataError` — each wrapping the correct HTTP status.
- **Traceable logging**: every request gets a short ID, with method, path, status and duration in milliseconds.
- **Externalised configuration** via `BaseSettings` and `.env`; no secrets in the repository.
- **Conventional commits** (`feat:`, `chore:`) across the entire history.
- **Continuous integration** on `push` and `pull_request` to `main` and `develop`.

### Actual state of test coverage

*76 test functions — state verified on 9 September 2026.*

| Suite | Tests | Scope | State |
|---|---:|---|---|
| `models/optimization` | 10 | EOQ, ROP, DTS, slow movers, holding cost | runnable |
| `models/analytics` | 5 | RFM scoring, segments, profitability, low margins | runnable |
| `models/forecasting` | 5 | Fit, predict, confidence intervals, misuse errors | runnable |
| `dashboard/tests` | 10 | Currency, percentage and date formatting, null handling | runnable |
| `backend/tests/test_api` | 16 | Product, order and inventory endpoints | **blocked** |
| `backend/tests/test_services` | 23 | Inventory, cost and metrics services | **blocked** |
| `backend/tests/test_crud` | 7 | Generic CRUD operations | **blocked** |

> **Verified defect — fix before submission**
>
> `backend/tests/conftest.py` line 10 imports `Product` and `InventorySnapshot` from `backend.models`. Both classes stopped being exported when the recipe schema landed on 15 June. The import fails at collection time, which prevents the **46 backend tests** from running at all. The same stale import breaks `scripts/load_sample_data.py`, and therefore sample-data loading.
>
> **Fix:** rewrite the fixtures around `RawMaterial`, `FinalProduct`, `Recipe` and `RecipeItem`. This is fixture redesign, not a rename: the service tests assume stock is carried by the product.

---

## 11. Project metrics

| Metric | Value |
|---|---:|
| Lines of Python | 6,449 |
| Source files | 103 |
| REST endpoints | 34 |
| Relational tables | 9 |
| Test functions | 76 |
| Alembic migrations | 3 |

### Code distribution by package

| Package | Code | Tests | Files | Role |
|---|---:|---:|---:|---|
| `backend/` | 3,206 | 431 | 61 | API, services, ORM, import |
| `dashboard/` | 1,746 | 44 | 21 | Streamlit interface |
| `models/` | 573 | 188 | 18 | Forecasting, optimisation, segmentation |
| `scripts/` | 261 | — | 3 | Initialisation, sample data, docs generation |
| **Total** | **5,786** | **663** | **103** | |

### Actual development timeline (Git history)

| Date | Milestone | Volume |
|---|---|---|
| 24 Apr 2026 | **Project scaffold** — full monorepo, 5 tables, API, dashboard, tests, CI | — |
| 12 May 2026 | Change-log cleanup | — |
| 12 May 2026 | **First CSV imports** — products and orders, import page | +703 / −53 |
| 13 May 2026 | **Inventory import** — stock updates, customer statistics, navigation gating | +513 / −119 |
| 15 Jun 2026 | **Recipe schema** — raw materials, bill of materials, transactions, 3 migrations, all 4 services rewritten | +2,375 / −906 |

That last commit alone accounts for **41% of every line changed in the project** and touches 24 files. It is the quantified argument behind the "pivot" section.

---

## 12. Limitations and future work

An internship report is judged as much on clear-sightedness as on delivery. Every limitation below was **verified in the code**, and each one converts directly into a future-work item.

| Severity | Limitation found | Future work |
|---|---|---|
| **Blocking** | **The backend test suite does not run.** `conftest.py` imports models deleted by the recipe migration: 46 tests fail at collection. | Rewrite the fixtures on the recipe schema and restore the 80% coverage target |
| **Blocking** | **The sample-data script is broken** for the same reason — it still creates `Product` rows. | Generate a synthetic dataset coherent with the bill of materials (materials, recipes, sizes) |
| Major | **Stock is never decremented by sales.** `current_stock` is only ever written by imports; the freshness of days-to-stockout depends on the last inventory upload. | Deduct consumed quantities when orders are imported, or keep a stock-movement ledger |
| Major | **Recipe cost is entered, not calculated.** `recipes.unit_cost` comes from the CSV; it is never recomputed as Σ(quantity × material cost), even though all the data needed is in the database. | Derive cost of goods from the bill of materials and recompute it whenever a material price changes |
| Major | **No authentication**; CORS open to all origins; single tenant. | OAuth2/JWT authentication, per-tenant isolation, origin restriction |
| Major | **The ARIMA model is refitted on every call** — four fits per request, with no persistence or caching. | Scheduled training, model serialisation, and a real background task behind `/forecasts/retrain`, which today only replies "queued" |
| Major | **Duplicated logic.** `models/optimization` and `models/analytics` are called by no endpoint: the backend services reimplement EOQ, ROP and margins. Only `models/forecasting` is actually wired in. | Make the services thin adapters over the `models/` package, and wire in the RFM segmentation that is already written and tested |
| Minor | **Action tracking is ephemeral.** `POST /recommendations/apply` persists nothing; state lives in the Streamlit session. | A recommendation-tracking table with status, date and author |
| Minor | **Potential savings are extracted by regular expression** from the English text of each recommendation. | Expose a dedicated numeric field in the recommendation payload |
| Minor | **The architecture documentation is stale**: `docs/architecture.md` still describes the five v1 tables. | Regenerate the documentation and fold in the recipe schema |
| Minor | **Currency and locale are fixed**: the currency symbol is hard-coded. | Make currency and number formatting configurable (relevant for a Tunisian deployment) |
| Minor | **Manual import only**: no synchronisation with a point-of-sale system. | Shopify/WooCommerce connectors or webhooks, explicitly deferred to phase 2 by the requirements document |

> **How to frame this in the report**
>
> Do not present these as failures. The expected framing is **acknowledged technical debt**: "the data-model change of 15 June was carried through the entire application chain — migrations, services, API, interface — but the test suite and utility scripts have not yet been realigned, which constitutes the first identified work item." That is an engineer's observation, not a confession.

---

## 13. Report structure

The canonical structure of a Tunisian second-year internship report, with the VendorIO content to place in each part. Target length for a second year: **30 to 45 pages** excluding appendices. French section names are given alongside, since the template itself is French.

### Front matter

| Element | Content |
|---|---|
| Cover page — *page de garde* | Institution, host company logo, title, academic and industrial supervisors, academic year |
| Acknowledgements — *remerciements* | Company supervisor, academic supervisor, host team |
| Table of contents | Auto-generated, two levels deep |
| List of figures / tables | Numbered by chapter: Figure 3.2, Table 4.1… |
| List of acronyms | API, REST, ORM, EOQ, ROP, DTS, COGS, MAPE, ARIMA, RFM, CI/CD, JSONB, CRUD, BOM, MVP |
| Abstract — *résumé* | Many Tunisian schools require a French (and sometimes Arabic) abstract even for an English report — check your school's template |

### Body of the report

| Chapter | Sections | VendorIO material to draw on | Pages |
|---|---|---|---:|
| **General introduction** | — | Internship context, problem statement in three sentences, outline of the report | 1–2 |
| **Ch. 1** — General framework *(cadre général)* | Host organisation · Context · Review of existing solutions · Critique · Proposed solution · Methodology | All of §2: business problem, competitor table, VendorIO's niche. Methodology: iterative development, conventional commits, continuous integration | 6–8 |
| **Ch. 2** — Requirements analysis *(analyse et spécification)* | Actors · Functional requirements · Non-functional requirements · Use cases · Backlog | Actor table (§2). Functional: the 6 pages (§8). Non-functional: response time < 500 ms, MAPE < 10%, coverage > 80%, Docker portability | 6–8 |
| **Ch. 3** — Design *(conception)* | Architecture · Data model · Diagrams · Technology choices | **The densest chapter.** §4 (3-tier, layering), §5 (9 tables, cardinalities, cost snapshot), §3 (the v1→v2 pivot — this is where it earns its value), §9 (justifications) | 8–12 |
| **Ch. 4** — Implementation *(réalisation)* | Environment · Import pipeline · Algorithms · Interfaces · Testing | §6 (pipeline, 1,029 lines), §7 (formulas and the worked example), screenshots of the 6 pages, §10 (quality and testing), §11 (metrics) | 10–14 |
| **Conclusion and future work** | — | Technical assessment, personal takeaways, §12 turned into a roadmap | 2–3 |
| **References** | — | Documentation for FastAPI, SQLAlchemy, Streamlit, statsmodels, Alembic, Poetry, Plotly | 1 |
| **Appendices** | — | CSV templates, an extract of the OpenAPI schema, `docker-compose.yml`, annotated migration `001` | — |

> **Three angles that separate a good report from an average one**
>
> **1. Tell the story of the pivot.** Most reports describe a system as if it were born perfect. Explaining why the "product" model was wrong, what it cost to change it, and what the bill of materials unlocked is what demonstrates engineering judgement.
>
> **2. Show the numbers.** Carry the Arabica bean example (§7) through end to end: 1,080 g/day, 18.5 days to stockout, 91 kg economic order quantity. A report that shows one complete calculation beats a report that quotes six formulas.
>
> **3. Own the limitations.** §12 is an asset, not a weakness: it proves you can audit your own code.

---

## 14. Figures to produce

A Tunisian report at this level typically carries **15 to 25 figures**. These are the ones derivable directly from the project.

| # | Figure | Chapter | Source / tool |
|---:|---|---|---|
| 1 | 3-tier architecture | Ch. 3 | §4 · draw.io |
| 2 | Package diagram (monorepo) | Ch. 3 | Repository tree · draw.io |
| 3 | Use-case diagram | Ch. 2 | Actor table §2 · StarUML / PlantUML |
| 4 | Class diagram / logical data model | Ch. 3 | §5 — 9 tables and cardinalities · StarUML |
| 5 | PostgreSQL relational schema | Ch. 3 | Export from pgAdmin or DBeaver |
| 6 | Sequence diagram "Import a CSV" | Ch. 3 | Browser → Streamlit → FastAPI → service → PostgreSQL |
| 7 | Sequence diagram "View alerts" | Ch. 3 | Include the TTL cache and the rules engine |
| 8 | Activity diagram of the import pipeline | Ch. 4 | §6 — the 9 steps and the rejection points |
| 9 | v1 versus v2 model comparison | Ch. 3 | §3 — an original figure, high value |
| 10 | Gantt chart | Ch. 1 | §11 — real dates from the Git history |
| 11–16 | Screenshots of the 6 dashboard pages | Ch. 4 | The running application, with data loaded |
| 17 | Forecast curve with confidence band | Ch. 4 | Forecasts page, MAPE visible |
| 18 | Turnover × days-to-stockout scatter | Ch. 4 | Inventory page — illustrates the status classification |
| 19 | Swagger documentation screenshot | Ch. 4 | `localhost:8000/docs` |
| 20 | Test coverage report | Ch. 4 | `pytest --cov --cov-report=html` *(after fixing §12)* |
| 21 | Continuous integration workflow run | Ch. 4 | GitHub Actions tab |

---

## 15. Glossary

Domain and technical terms to define once and then use consistently — terminology drift is a classic criticism in a viva. The French column is kept because most Tunisian schools require a French abstract, and because the oral defence may be conducted in French.

| English (code) | Definition | French equivalent |
|---|---|---|
| raw material | What the business buys and stocks | **matière première** |
| final product | What the business sells | **produit fini** |
| bill of materials (BOM) | The recipe linking a product to its materials and quantities | **nomenclature** (or recette) |
| economic order quantity | Order size minimising ordering plus holding cost | **quantité économique de commande** — also the **formule de Wilson** |
| reorder point | Stock level triggering a new purchase order | **point de commande** / seuil de réapprovisionnement |
| holding cost | Annual cost of keeping one unit in stock | **coût de possession** / coût de stockage |
| ordering cost | Fixed cost per purchase order placed | **coût de passation** |
| stockout | Running out of a material, halting production | **rupture de stock** |
| days to stockout | Stock on hand divided by daily consumption | **jours avant rupture** / couverture de stock |
| inventory turnover | How many times stock is consumed per year | **rotation des stocks** |
| slow mover | Item in the bottom quartile of turnover | **article à rotation lente** / dormant |
| overstock | More than 180 days of stock on hand | **surstock** |
| lead time | Days between placing an order and receiving it | **délai d'approvisionnement** |
| COGS | Cost of goods sold, from frozen unit costs | **coût des marchandises vendues** |
| gross margin | (Revenue − COGS) ÷ Revenue | **marge brute** |
| demand forecasting | Predicting future sales from history | **prévision de la demande** |
| time series | Values indexed by regular time steps | **série temporelle** / chronologique |
| confidence interval | Range containing the true value at a stated probability — 80% here | **intervalle de confiance** |
| MAPE | Mean absolute percentage error, the forecast accuracy metric | **erreur absolue moyenne en pourcentage** |
| RFM segmentation | Customer scoring on recency, frequency and monetary value | **segmentation RFM** (récence, fréquence, montant) |
| cost snapshot | Unit cost frozen on the order line at import time | **coût figé** |
| endpoint | A single addressable HTTP route of the API | **point d'accès** / route |
| dependency injection | Supplying a component's collaborators from outside it | **injection de dépendance** |
| migration | A versioned, scripted change to the database schema | **migration de schéma** |
| single-tenant | One deployment serves exactly one business | **mono-locataire** |

---

*Compiled by repository audit · branch `main` · commit `9b4f74c` · 9 September 2026*
