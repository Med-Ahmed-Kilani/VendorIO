# Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│                 localhost:8501                                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (httpx)
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│                 localhost:8000                                │
└────┬──────────────────────────────────────────────────────┬─┘
     │ SQLAlchemy ORM                              │ Python calls
┌────▼──────────────────────┐          ┌────────────────────▼──┐
│   ML/Analytics Models     │          │    PostgreSQL DB      │
│  (forecasting, optimize)  │          │  localhost:5432       │
└────────────────────────────┘          └───────────────────────┘
```

## Layer Responsibilities

| Layer | Path | Responsibility |
|-------|------|----------------|
| **API Routes** | `backend/api/v1/` | HTTP request handling, validation, response shaping |
| **Services** | `backend/services/` | Business logic, KPI calculations, recommendation rules |
| **CRUD** | `backend/crud/` | Database access patterns, query building |
| **Models** | `backend/models/` | SQLAlchemy ORM table definitions |
| **Schemas** | `backend/schemas/` | Pydantic request/response contracts |
| **ML Models** | `models/` | Forecasting, optimization, segmentation algorithms |
| **Dashboard** | `dashboard/` | Streamlit pages, charts, API calls |

## Database Schema

5 core tables: `products`, `orders`, `order_items`, `customers`, `inventory_snapshots`

JSONB used for `products.attributes`, `orders.metadata`, `customers.customer_attributes` — allowing schema flexibility without migrations.

## Key Design Decisions

1. **Sync SQLAlchemy** — simpler than async for analytics workloads with no high-concurrency requirement
2. **ARIMA over Prophet** — no C++ build dependency, lighter to install
3. **Rules-based recommendations** — interpretable, fast, no model training required
4. **Streamlit + httpx** — clean separation between dashboard and API
