# VendorIO Documentation

Welcome to VendorIO — a modular analytics platform for small e-commerce businesses.

## What it does

- **Business Overview** — revenue KPIs, top products, customer cohorts
- **Inventory Optimization** — reorder alerts, EOQ, slow-mover detection
- **Cost Analysis** — margin breakdown, holding cost forecasts
- **Demand Forecasting** — ARIMA-based 4-week revenue + product forecasts
- **Smart Alerts** — auto-generated, prioritized action items

## Quick start

```bash
cp .env.example .env
docker-compose up -d postgres
poetry install
python scripts/init_db.py
python scripts/load_sample_data.py
uvicorn backend.main:app --reload   # terminal 1
streamlit run dashboard/app.py      # terminal 2
```

- Dashboard → http://localhost:8501
- API → http://localhost:8000
- Swagger → http://localhost:8000/docs
