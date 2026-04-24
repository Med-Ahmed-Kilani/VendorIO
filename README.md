# VendorIO — Small Business E-Commerce Analytics Platform

A modular, production-ready analytics platform for small business owners to optimize inventory, reduce costs, and forecast demand.

## Features

- **Business Overview Dashboard** — KPIs, top products, customer metrics
- **Inventory Optimization** — Stock levels, turnover, reorder recommendations
- **Cost Analysis** — Margins, holding costs, reduction opportunities
- **Demand Forecasting** — 4-week revenue + product-level forecasts
- **Smart Alerts & Recommendations** — Automated action items

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL 15 |
| ML | scikit-learn, statsmodels |
| Packaging | Poetry |

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo>
cd small-business-analytics

# 2. Copy environment file
cp .env.example .env

# 3. Start PostgreSQL
docker-compose up -d postgres

# 4. Install dependencies
poetry install

# 5. Initialize database and load sample data
python scripts/init_db.py
python scripts/load_sample_data.py

# 6. Run backend (terminal 1)
uvicorn backend.main:app --reload

# 7. Run dashboard (terminal 2)
streamlit run dashboard/app.py
```

Or use Docker Compose to run everything:
```bash
docker-compose up
```

- Dashboard: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development

```bash
# Run tests
pytest

# Lint
ruff check .
black --check .

# Create DB migration
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Project Structure

```
├── backend/          # FastAPI application
├── models/           # ML/analytics models
├── dashboard/        # Streamlit dashboard
├── data/             # Sample data and seed SQL
├── scripts/          # Utility scripts
├── docs/             # Documentation
└── .github/          # CI/CD workflows
```
