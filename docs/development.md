# Development Guide

## Setup

```bash
# 1. Clone and enter project
git clone <repo-url>
cd vendorio

# 2. Environment
cp .env.example .env
# Edit .env with your DB credentials

# 3. Dependencies
pip install poetry
poetry install

# 4. Start PostgreSQL
docker-compose up -d postgres

# 5. Initialize database
python scripts/init_db.py

# 6. Load sample data
python scripts/load_sample_data.py
# Or with Kaggle dataset:
# python scripts/load_sample_data.py --csv data/Online_Retail.csv

# 7. Run services
uvicorn backend.main:app --reload          # API on :8000
streamlit run dashboard/app.py             # Dashboard on :8501
```

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=backend --cov=models --cov-report=html

# Run specific test file
pytest backend/tests/test_services/test_inventory_service.py -v
```

## Linting

```bash
ruff check .
black --check .
# Auto-fix:
ruff check . --fix
black .
```

## Database Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add field to products"

# Apply all pending migrations
alembic upgrade head

# Roll back one
alembic downgrade -1
```

## Project Structure

```
backend/
  api/v1/          # FastAPI routes
  crud/            # DB access layer
  models/          # SQLAlchemy ORM
  schemas/         # Pydantic models
  services/        # Business logic
  tests/           # pytest tests

models/            # ML algorithms
  forecasting/     # ARIMA demand forecast
  optimization/    # EOQ, ROP, slow-movers
  analytics/       # RFM segmentation, profitability

dashboard/
  pages/           # Streamlit pages (5 tabs)
  components/      # Reusable chart/table/KPI components
  utils/           # API client, formatters, cache
```

## Adding a New API Endpoint

1. Add route in `backend/api/v1/<module>.py`
2. Add business logic in `backend/services/`
3. Add CRUD queries in `backend/crud/`
4. Add Pydantic schemas in `backend/schemas/`
5. Wire up in `backend/main.py`
6. Write test in `backend/tests/test_api/`
