# Small Business E-Commerce Analytics Platform
## Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** April 2026  
**Author:** Ahmed  
**Status:** Ready for Implementation  

---

## 1. Executive Summary

A modular, production-ready analytics platform for small business owners to optimize inventory, reduce costs, and forecast demand. Built as a monorepo with separate concerns: backend API, ML models, and Streamlit dashboard. Designed for scalability and extensibility to support the larger small business analytics platform.

**Core Value Proposition:**
- Real-time inventory optimization and cost reduction
- Demand forecasting with actionable alerts
- Product profitability analysis
- Zero vendor lock-in (flexible DB, open source tech stack)

---

## 2. Project Scope & MVP Definition

### MVP Features
1. **Business Overview Dashboard** - KPIs, top products, customer metrics
2. **Inventory Optimization** - Stock levels, turnover, reorder recommendations
3. **Cost Analysis** - Margins, holding costs, reduction opportunities
4. **Demand Forecasting** - 4-week revenue + product-level forecasts
5. **Smart Alerts & Recommendations** - Automated action items for business owners

### Out of Scope (Phase 2)
- Real-time order syncing with e-commerce platforms
- Multi-tenant support (single-tenant MVP)
- Mobile app
- Advanced ML (deep learning, anomaly detection)

---

## 3. Technical Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│          (Visualization, User Interaction, Reports)          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│          (REST API, Business Logic, Data Validation)         │
└────┬──────────────────────────────────────────────────────┬─┘
     │                                                         │
┌────▼──────────────────────┐          ┌────────────────────▼──┐
│   ML/Analytics Models     │          │    PostgreSQL DB      │
│  (Forecasting, Optimize)  │          │  (Flexible Schema)    │
└────────────────────────────┘          └───────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Frontend** | Streamlit | Rapid iteration, built-in UI components, perfect for data viz |
| **Backend** | FastAPI + Python 3.11+ | Async, type hints, auto-docs (Swagger), fast |
| **Database** | PostgreSQL 15+ | JSONB for schema flexibility, reliability, ACID compliance |
| **Models** | scikit-learn, statsmodels, Prophet | Lightweight, interpretable, no GPU dependency |
| **Package Manager** | Poetry | Reproducible builds, lock files, dependency isolation |
| **Testing** | pytest + pytest-cov | Industry standard, fixture support |
| **Linting/Formatting** | ruff + black | Fast, modern Python tooling |
| **Container** | Docker + Docker Compose | Local dev = prod environment |
| **CI/CD** | GitHub Actions | Native, no setup cost |
| **Documentation** | MkDocs | Auto-generate from code + markdown |

---

## 4. Project Structure (Monorepo)

```
small-business-analytics/
├── README.md
├── pyproject.toml              # Poetry config (all packages)
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Dev environment
├── .github/
│   └── workflows/
│       ├── test.yml            # Run tests on push
│       ├── lint.yml            # Linting checks
│       └── deploy.yml          # (Phase 2)
├── .env.example                # Environment variables template
├── .gitignore
│
├── backend/                    # FastAPI Application
│   ├── __init__.py
│   ├── main.py                 # App initialization, startup/shutdown
│   ├── config.py               # Settings (BaseSettings from Pydantic)
│   ├── dependencies.py         # Dependency injection (DB sessions, auth)
│   ├── middleware.py           # CORS, error handling, logging
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── orders.py       # /api/v1/orders - CRUD endpoints
│   │   │   ├── products.py     # /api/v1/products
│   │   │   ├── inventory.py    # /api/v1/inventory
│   │   │   ├── metrics.py      # /api/v1/metrics - calculations
│   │   │   ├── forecasts.py    # /api/v1/forecasts
│   │   │   └── recommendations.py  # /api/v1/recommendations
│   │   └── health.py           # /health - liveness probe
│   │
│   ├── models/                 # SQLAlchemy ORM Models
│   │   ├── __init__.py
│   │   ├── base.py             # Base model with timestamps
│   │   ├── order.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   └── customer.py
│   │
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── order.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   └── common.py           # Shared (pagination, etc.)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Database connection setup
│   │   └── migrations/         # Alembic migrations
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   │
│   ├── crud/                   # Database operations (C-R-U-D)
│   │   ├── __init__.py
│   │   ├── base.py             # Generic CRUD class
│   │   ├── order.py
│   │   ├── product.py
│   │   └── inventory.py
│   │
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── inventory_service.py   # Inventory calc, reorder logic
│   │   ├── cost_service.py        # Cost analysis, margins
│   │   ├── metrics_service.py     # KPI calculations
│   │   └── recommendation_service.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging setup
│   │   └── errors.py           # Custom exceptions
│   │
│   └── tests/
│       ├── conftest.py         # Pytest fixtures
│       ├── test_api/
│       │   ├── test_orders.py
│       │   ├── test_products.py
│       │   └── test_inventory.py
│       ├── test_services/
│       │   ├── test_inventory_service.py
│       │   ├── test_cost_service.py
│       │   └── test_metrics_service.py
│       └── test_crud/
│           └── test_crud_operations.py
│
├── models/                     # ML/Analytics Models
│   ├── __init__.py
│   ├── requirements.txt        # ML-specific deps (if separate)
│   │
│   ├── forecasting/
│   │   ├── __init__.py
│   │   ├── time_series.py      # ARIMA, Prophet wrappers
│   │   ├── demand_forecast.py  # Product-level demand
│   │   └── tests/
│   │       └── test_forecasting.py
│   │
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── inventory.py        # EOQ, ROP, slow-mover detection
│   │   ├── pricing.py          # Margin optimization (Phase 2)
│   │   └── tests/
│   │       └── test_optimization.py
│   │
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── segmentation.py     # Customer segmentation
│   │   ├── profitability.py    # Product profit analysis
│   │   └── tests/
│   │       └── test_analytics.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── data_loader.py      # Load from DB/CSV
│       └── validators.py       # Data validation
│
├── dashboard/                  # Streamlit Application
│   ├── __init__.py
│   ├── app.py                  # Main Streamlit entry point
│   ├── config.py               # Dashboard config (colors, themes)
│   │
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── 1_overview.py       # Business overview (home)
│   │   ├── 2_inventory.py      # Inventory optimization
│   │   ├── 3_costs.py          # Cost analysis
│   │   ├── 4_forecasts.py      # Demand forecasts
│   │   └── 5_alerts.py         # Smart alerts & recommendations
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── sidebar.py          # Sidebar filters, navigation
│   │   ├── kpi_cards.py        # Reusable KPI display
│   │   ├── charts.py           # Reusable chart functions
│   │   └── tables.py           # Reusable table components
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── api_client.py       # HTTP calls to backend
│   │   ├── formatters.py       # Number/date formatting
│   │   └── cache.py            # Streamlit caching
│   │
│   ├── styles/
│   │   ├── __init__.py
│   │   └── theme.css           # Custom Streamlit theme (optional)
│   │
│   └── tests/
│       └── test_components.py  # (Light testing for UI logic)
│
├── data/                       # Sample/test data
│   ├── sample_dataset.csv      # Kaggle Online Retail (anonymized)
│   └── seed_data.sql           # Initial DB setup
│
├── docs/                       # Documentation
│   ├── index.md
│   ├── architecture.md
│   ├── api_reference.md        # Auto-generated from code
│   ├── deployment.md
│   ├── development.md
│   └── mkdocs.yml
│
└── scripts/                    # Utility scripts
    ├── init_db.py              # Initialize PostgreSQL
    ├── load_sample_data.py     # Populate with Kaggle data
    └── generate_docs.py        # Auto-gen API docs
```

---

## 5. Database Schema (PostgreSQL with JSONB Flexibility)

### Why PostgreSQL + JSONB?
- **Flexibility:** Store arbitrary product attributes (color, size, tags) in JSONB without schema migration
- **Queryability:** Can query JSONB fields like `attributes->>'color' = 'red'`
- **Reliability:** ACID compliance, powerful for financial data (orders, revenue)
- **Scalability:** Handles small → medium business growth easily

### Core Tables

```sql
-- Timestamps & soft deletes on all tables
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_price DECIMAL(10,2) NOT NULL,
    cost_per_unit DECIMAL(10,2),
    current_stock INT DEFAULT 0,
    lead_time_days INT DEFAULT 7,
    reorder_point INT,
    attributes JSONB DEFAULT '{}',  -- flexible schema for product variations
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_date TIMESTAMP NOT NULL,
    customer_id INT,
    total_amount DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'completed',
    metadata JSONB DEFAULT '{}',  -- shipping, payment method, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2),
    UNIQUE(order_id, product_id)
);

CREATE TABLE inventory_snapshots (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id),
    stock_level INT,
    holding_cost DECIMAL(10,2),
    snapshot_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    first_order_date DATE,
    total_spent DECIMAL(12,2),
    order_count INT DEFAULT 0,
    customer_attributes JSONB DEFAULT '{}',  -- geographic, behavioral data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_inventory_snapshots_product_date ON inventory_snapshots(product_id, snapshot_date);
CREATE INDEX idx_customers_email ON customers(email);
```

---

## 6. API Specification (FastAPI)

### Base URL
```
http://localhost:8000/api/v1
```

### Core Endpoints

#### **Orders**
```
GET /orders?start_date=2024-01-01&end_date=2024-12-31&skip=0&limit=100
POST /orders
GET /orders/{order_id}
PUT /orders/{order_id}
DELETE /orders/{order_id}

Response (GET /orders):
{
  "data": [
    {
      "id": 1,
      "order_date": "2024-01-15T10:30:00Z",
      "customer_id": 42,
      "total_amount": 125.50,
      "items": [
        {"product_id": 1, "quantity": 2, "unit_price": 50.00}
      ],
      "status": "completed"
    }
  ],
  "total": 500,
  "skip": 0,
  "limit": 100
}
```

#### **Products**
```
GET /products?category=coffee&skip=0&limit=100
POST /products
GET /products/{product_id}
PUT /products/{product_id}
DELETE /products/{product_id}
```

#### **Inventory**
```
GET /inventory/status
  → Current stock levels, turnover rates, reorder points

GET /inventory/{product_id}/health
  → Days to stockout, holding cost, turnover rank

POST /inventory/sync
  → Recalculate all inventory metrics
```

#### **Metrics** (Aggregated KPIs)
```
GET /metrics/kpi?period=monthly&start_date=2024-01-01&end_date=2024-12-31
  → {
      "total_revenue": 50000,
      "total_profit": 15000,
      "order_count": 300,
      "avg_order_value": 166.67,
      "repeat_customer_rate": 0.35,
      "top_products": [...],
      "bottom_products": [...]
    }

GET /metrics/customer-segments
  → Customer cohorts by AOV, repeat rate, lifetime value

GET /metrics/profitability
  → Margin analysis by product, category
```

#### **Forecasts**
```
GET /forecasts/revenue?weeks_ahead=4
  → {
      "forecast": [
        {"week": "2024-05-01", "revenue": 12500, "ci_lower": 11000, "ci_upper": 14000}
      ],
      "model": "prophet",
      "mape": 0.05
    }

GET /forecasts/demand?product_id=1&weeks_ahead=4
  → Product-level demand forecast

POST /forecasts/retrain
  → Re-train all forecasting models
```

#### **Recommendations**
```
GET /recommendations?limit=10
  → {
      "recommendations": [
        {
          "type": "slow_mover",
          "product_id": 5,
          "product_name": "Green Tea",
          "action": "Consider discontinuing or bundling",
          "impact": "Reduce holding cost by $50/month",
          "urgency": "high"
        },
        {
          "type": "stockout_risk",
          "product_id": 2,
          "days_remaining": 5,
          "action": "Reorder immediately",
          "urgency": "critical"
        }
      ]
    }

POST /recommendations/apply
  → Mark recommendation as "applied" for tracking
```

#### **Health & Status**
```
GET /health
  → {"status": "healthy", "db": "connected", "timestamp": "..."}
```

### Error Handling
All endpoints return consistent error format:
```json
{
  "detail": "Description of error",
  "status_code": 400,
  "error_code": "INVALID_DATE_RANGE"
}
```

---

## 7. ML Models Specification

### 7.1 Demand Forecasting

**Input:**
- Historical order data (minimum 8-12 weeks)
- Product ID (or aggregate revenue)

**Output:**
- 4-week forecast with confidence intervals
- Model: Prophet (robust to missing data, seasonality)
- Metrics: MAPE (Mean Absolute Percentage Error) < 10%

**Code Structure:**
```python
# models/forecasting/demand_forecast.py
class DemandForecaster:
    def __init__(self, product_id: int):
        self.product_id = product_id
        self.model = None
    
    def fit(self, historical_data: pd.DataFrame):
        # historical_data: (date, sales_quantity/revenue)
        pass
    
    def predict(self, periods: int = 28) -> pd.DataFrame:
        # Returns forecast with yhat, yhat_lower, yhat_upper
        pass
```

### 7.2 Inventory Optimization

**Key Calculations:**

1. **Reorder Point (ROP):**
   ```
   ROP = Lead Time × Average Daily Demand
   ```

2. **Economic Order Quantity (EOQ):**
   ```
   EOQ = √(2 × D × S / H)
   Where:
     D = Annual demand
     S = Ordering cost per order
     H = Holding cost per unit per year
   ```

3. **Days to Stockout:**
   ```
   DTS = Current Stock / Average Daily Sales
   ```

4. **Slow-Mover Detection:**
   ```
   IF Turnover Rate < (Median Turnover - 1σ) THEN Slow Mover
   ```

**Code Structure:**
```python
# models/optimization/inventory.py
class InventoryOptimizer:
    @staticmethod
    def calculate_reorder_point(avg_daily_demand: float, lead_time_days: int) -> float:
        pass
    
    @staticmethod
    def calculate_eoq(annual_demand: int, ordering_cost: float, holding_cost_per_unit: float) -> float:
        pass
    
    @staticmethod
    def identify_slow_movers(products: List[Product], threshold_percentile: float = 25) -> List[int]:
        # Return product IDs in bottom 25% of turnover
        pass
```

### 7.3 Recommendation Engine

**Rules-Based Logic:**

```python
# models/recommendation_service.py
recommendations = []

# Rule 1: Slow movers
for product in slow_movers:
    recommendations.append({
        "type": "slow_mover",
        "urgency": "medium",
        "action": f"Bundle {product.name} with fast-movers or discount 10-15%",
        "impact": f"Save ${product.holding_cost * 12} annual holding cost"
    })

# Rule 2: Stockout risk
for product in products:
    if product.days_to_stockout < 7:
        recommendations.append({
            "type": "stockout_risk",
            "urgency": "critical",
            "action": f"Reorder {product.reorder_quantity} units immediately",
            "impact": "Avoid lost sales"
        })

# Rule 3: Bulk order discount
for product in high_velocity_products:
    if bulk_discount_available:
        recommendations.append({
            "type": "bulk_order",
            "urgency": "low",
            "action": f"Order {bulk_quantity} units for 15% discount",
            "impact": f"Save ${savings} on COGS"
        })
```

---

## 8. Dashboard Pages (Streamlit)

### Page 1: Business Overview (Home)
**Components:**
- KPI cards: Revenue, Profit, Orders, Repeat Customer %
- Line chart: Revenue trend (30 days)
- Bar chart: Top 5 products by revenue
- Metric: Avg order value, customer segments

**Interactivity:**
- Date range picker (sidebar)
- Category filter
- Export as PDF/CSV

### Page 2: Inventory Optimization
**Components:**
- Table: All products with stock level, turnover, days-to-stockout (sortable, filterable)
- Heatmap: Inventory health (green = optimal, yellow = warning, red = critical)
- Highlight: Reorder recommendations with urgency
- Chart: Holding cost breakdown by product

**Actions:**
- Mark product as "reviewed" (acknowledges recommendation)
- Download reorder list (CSV for supplier)

### Page 3: Cost Analysis
**Components:**
- Stacked bar chart: COGS + Holding Cost + Other vs. Revenue by product
- Margin ranking: Products sorted by profit margin
- Alert: Products with negative or <10% margin
- Savings forecast: "If you implement recommendations, save $X/month"

### Page 4: Demand Forecasts
**Components:**
- Line chart: Revenue forecast 4 weeks with confidence band
- Product-level forecasts (dropdown selector)
- Model performance: MAPE, R², last update timestamp
- Alert: "High demand expected next week for Product X—consider increasing stock"

### Page 5: Smart Alerts & Recommendations
**Components:**
- Priority list: All recommendations sorted by urgency (critical → low)
- Action tracker: Status of applied recommendations
- Impact summary: Total potential savings if all recommendations implemented

**Interactivity:**
- Mark as "applied", "ignored", "pending"
- Comment section for business owner notes

---

## 9. Best Practices

### 9.1 Code Quality

**Linting & Formatting:**
```bash
# pyproject.toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]  # Errors, undefined, warnings, imports, naming

[tool.black]
line-length = 100
target-version = ['py311']

[tool.pytest.ini_options]
testpaths = ["backend/tests", "models/tests", "dashboard/tests"]
addopts = "--cov=backend --cov=models --cov-report=html"
```

**Run before commit:**
```bash
ruff check .
black --check .
pytest --cov
```

### 9.2 Type Hints
Every function must have type hints:
```python
# Good
def calculate_profit(revenue: float, cost: float) -> float:
    return revenue - cost

# Avoid
def calculate_profit(revenue, cost):
    return revenue - cost
```

### 9.3 Documentation

**Docstrings (Google style):**
```python
def reorder_point(avg_daily_demand: float, lead_time_days: int) -> float:
    """Calculate reorder point for inventory.
    
    Args:
        avg_daily_demand: Average units sold per day.
        lead_time_days: Days to receive new shipment from supplier.
    
    Returns:
        Reorder point in units.
    
    Example:
        >>> reorder_point(5.0, 7)
        35.0
    """
    return avg_daily_demand * lead_time_days
```

### 9.4 Testing

**Unit Tests (pytest):**
```python
# backend/tests/test_services/test_inventory_service.py
import pytest
from backend.services import InventoryService

@pytest.fixture
def sample_product():
    return Product(id=1, name="Coffee", cost=5.0, current_stock=100)

def test_calculate_reorder_point(sample_product):
    result = InventoryService.calculate_reorder_point(
        avg_daily_demand=10.0,
        lead_time_days=7
    )
    assert result == 70.0

def test_identify_slow_movers(sample_products):
    slow = InventoryService.identify_slow_movers(sample_products)
    assert len(slow) > 0
    assert all(p.turnover_rate < threshold for p in slow)
```

**Coverage target:** >80% for critical paths (services, models)

### 9.5 Database Migrations (Alembic)
```bash
# Create new migration after schema changes
alembic revision --autogenerate -m "Add reorder_point to products"

# Apply migrations
alembic upgrade head
```

### 9.6 Logging

```python
# backend/utils/logger.py
import logging

logger = logging.getLogger(__name__)

# In code:
logger.info(f"Loaded {len(orders)} orders")
logger.error(f"Database connection failed: {error}")
```

### 9.7 Environment Management

**.env.example:**
```
DATABASE_URL=postgresql://user:password@localhost:5432/analytics_db
FASTAPI_ENV=development
LOG_LEVEL=INFO
FORECAST_RETRAIN_DAYS=7
```

**Never commit secrets!** Use `.env` locally, vault in production.

### 9.8 Error Handling

```python
from fastapi import HTTPException, status

try:
    product = await crud.product.get(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )
```

### 9.9 API Documentation
FastAPI auto-generates OpenAPI docs:
```
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

Decorate endpoints:
```python
@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductResponse:
    """
    Retrieve a product by ID.
    
    - **product_id**: The unique product identifier
    """
```

---

## 10. Development Workflow

### 10.1 Local Setup
```bash
# Clone & navigate
git clone <repo>
cd small-business-analytics

# Create virtual environment & install dependencies
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install poetry
poetry install

# Set up database
cp .env.example .env
docker-compose up -d postgres
python scripts/init_db.py

# Load sample data
python scripts/load_sample_data.py

# Run backend
cd backend && uvicorn main:app --reload

# Run dashboard (new terminal)
cd dashboard && streamlit run app.py
```

### 10.2 Git Workflow
```bash
# Feature branch
git checkout -b feature/inventory-alerts

# Commit with conventional commits
git commit -m "feat(inventory): add slow-mover detection"

# Push & create PR
git push origin feature/inventory-alerts
```

**Conventional Commits Format:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code restructure
- `docs:` Documentation
- `test:` Tests
- `chore:` Maintenance

### 10.3 CI/CD Pipeline (GitHub Actions)

**.github/workflows/test.yml:**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: poetry install
      - run: pytest --cov
```

---

## 11. Deployment Strategy (Phase 2)

### Local/Development:
```bash
docker-compose up
# Access dashboard at http://localhost:8501
# Access API at http://localhost:8000
```

### Production (Future):
- **Backend:** AWS ECS / Railway.app with PostgreSQL RDS
- **Dashboard:** Streamlit Cloud or AWS S3 + CloudFront
- **Database:** AWS RDS PostgreSQL (managed, auto-backup)
- **Monitoring:** CloudWatch / DataDog for logs & metrics

---

## 12. Success Metrics

**Technical:**
- Test coverage >80%
- API response time <500ms
- Dashboard load time <3s
- Forecast MAPE <10%

**Business (for demonstration):**
- Identify cost-saving opportunities worth >$500/month on sample data
- Generate 10+ actionable recommendations per business
- Forecast accuracy validated against holdout test set

---

## 13. Timeline & Milestones (4 Weeks)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1 | Backend setup + DB schema | FastAPI running, Postgres init, basic CRUD |
| 2 | Core APIs + Services | /metrics, /inventory, /products endpoints live |
| 3 | ML Models + Dashboard | Forecasts working, all 5 pages functional |
| 4 | Testing + Polish | >80% test coverage, deploy instructions, docs |

---

## 14. Open Questions / Decisions

1. **Data Source:** Use Kaggle Online Retail dataset or create synthetic data?
   - **Decision:** Kaggle (real, no mock data)

2. **Holding Cost Model:** Fixed $/unit/month or % of COGS?
   - **Decision:** Support both, configurable per product

3. **Forecast Granularity:** Aggregate revenue or product-level demand?
   - **Decision:** Both (aggregate for dashboard, product-level on demand)

4. **Real-Time Syncing (Phase 2):** Webhooks from Shopify/WooCommerce?
   - **Decision:** Out of scope for MVP, design for extensibility

---

## 15. References & Resources

- **FastAPI:** https://fastapi.tiangolo.com/
- **Streamlit:** https://docs.streamlit.io/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Prophet Forecasting:** https://facebook.github.io/prophet/
- **Poetry:** https://python-poetry.org/
- **Pytest:** https://docs.pytest.org/

---

**Document Status:** Ready for implementation  
**Next Step:** Provide this PRD to Claude Code for full project scaffolding and initial development.
