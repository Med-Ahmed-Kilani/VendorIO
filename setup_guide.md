# Small Business Analytics Platform
## Local Development & Setup Guide

---

## 1. Project Naming Options

Here are some name suggestions that fit the vibe:

| Name | Character | Best For |
|------|-----------|----------|
| **InventoryOS** | Modern, systems-focused | Emphasizes inventory optimization |
| **VendorIO** | Clean, tech-forward | I/O (input/output) for business data |
| **ProfitFlow** | Direct, business-focused | Revenue & cost optimization |
| **StockWise** | Simple, smart | Inventory management angle |
| **AnalyticHub** | Professional, accessible | Central analytics platform |
| **MetricsFlow** | Technical, modern | Data-driven operations |

**My recommendation:** **InventoryOS** — feels like a complete operating system for small businesses, memorable, and aligns with your "clean, understated" aesthetic.

---

## 2. Quick Start (TL;DR)

```bash
# 1. Create project folder
mkdir InventoryOS
cd InventoryOS

# 2. Initialize Git
git init
git config user.name "Ahmed"
git config user.email "your.email@example.com"

# 3. Create initial structure
mkdir backend dashboard models data docs scripts tests
touch .gitignore .env.example README.md pyproject.toml

# 4. Open in VS Code
code .

# 5. Open Claude Code terminal in VS Code
# Then provide the PRD file

# 6. Let Claude Code scaffold the full structure
```

---

## 3. Step-by-Step Setup

### Step 1: Create Project Directory & Initialize Git

```bash
# Create project
mkdir InventoryOS
cd InventoryOS
git init

# Create basic structure
touch .gitignore README.md pyproject.toml .env.example

# Create subdirectories
mkdir -p backend dashboard models data scripts docs
mkdir -p backend/tests backend/api backend/models backend/schemas backend/services backend/crud backend/db backend/utils
mkdir -p models/forecasting models/optimization models/analytics models/utils
mkdir -p dashboard/pages dashboard/components dashboard/utils dashboard/styles
```

### Step 2: Create `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local

# Database
*.db
*.sqlite
*.sqlite3

# Testing
.pytest_cache/
.coverage
htmlcov/

# Data
data/raw/
data/processed/

# Logs
logs/
*.log

# Cache
.streamlit/
.cache/
```

### Step 3: Create Initial `pyproject.toml`

```toml
[tool.poetry]
name = "inventory-os"
version = "0.1.0"
description = "E-commerce analytics and inventory optimization platform for small businesses"
authors = ["Ahmed <your.email@example.com>"]
readme = "README.md"
packages = [
    { include = "backend" },
    { include = "models" },
    { include = "dashboard" }
]

[tool.poetry.dependencies]
python = "^3.11"

# Backend
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
psycopg2-binary = "^2.9.0"  # PostgreSQL driver
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
python-dotenv = "^1.0.0"

# Data & ML
pandas = "^2.0.0"
numpy = "^1.24.0"
scikit-learn = "^1.3.0"
statsmodels = "^0.14.0"
prophet = "^1.1.5"
plotly = "^5.17.0"

# Frontend
streamlit = "^1.28.0"
requests = "^2.31.0"

# Development
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.11.0"
ruff = "^0.1.7"
mypy = "^1.7.0"

[tool.poetry.group.dev.dependencies]
ipython = "^8.17.0"
jupyter = "^1.0.0"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["backend/tests", "models/tests", "dashboard/tests"]
addopts = "--cov=backend --cov=models --cov-report=html -v"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Step 4: Create `.env.example`

```
# Database
DATABASE_URL=postgresql://analytics_user:analytics_password@localhost:5432/analytics_db
SQLALCHEMY_ECHO=True

# FastAPI
FASTAPI_ENV=development
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
CORS_ORIGINS=["http://localhost:8501", "http://localhost:3000"]

# ML/Forecasting
FORECAST_RETRAIN_DAYS=7
MIN_HISTORICAL_DAYS=56

# Logging
LOG_LEVEL=INFO

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Step 5: Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: analytics_db
    environment:
      POSTGRES_USER: analytics_user
      POSTGRES_PASSWORD: analytics_password
      POSTGRES_DB: analytics_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U analytics_user -d analytics_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  adminer:
    image: adminer
    container_name: analytics_adminer
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### Step 6: Create Initial `README.md`

```markdown
# InventoryOS

E-commerce analytics and inventory optimization platform for small businesses.

## Features

- **Business Overview** - KPIs, revenue trends, customer insights
- **Inventory Optimization** - Stock levels, turnover rates, reorder recommendations
- **Cost Analysis** - Profitability analysis, cost reduction opportunities
- **Demand Forecasting** - 4-week revenue and product-level forecasts
- **Smart Alerts** - Automated recommendations for action

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- PostgreSQL 15+ (or Docker)
- Git

### Setup (5 minutes)

1. **Clone & navigate:**
   ```bash
   cd InventoryOS
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install poetry
   poetry install
   ```

4. **Set up database:**
   ```bash
   cp .env.example .env
   docker-compose up -d postgres
   ```

5. **Initialize database:**
   ```bash
   python scripts/init_db.py
   python scripts/load_sample_data.py
   ```

6. **Run backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   # Open http://localhost:8000/docs
   ```

7. **Run dashboard (new terminal):**
   ```bash
   cd dashboard
   streamlit run app.py
   # Opens http://localhost:8501
   ```

## Project Structure

See `docs/architecture.md` for detailed structure.

## Development

### Format & Lint
```bash
black .
ruff check .
```

### Run Tests
```bash
pytest --cov
```

### Create Database Migration
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## API Documentation

Once backend is running:
- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Deployment

See `docs/deployment.md` for production setup.

## License

MIT

## Contact

Ahmed - Data Science Engineering, University Project
```

---

## 4. Running the Project Locally

### First-Time Setup (One-time)

```bash
# 1. Start database
docker-compose up -d postgres

# 2. Wait for PostgreSQL to be ready (check health)
docker-compose ps

# 3. Install dependencies
poetry install

# 4. Initialize database schema
python scripts/init_db.py

# 5. Load sample data
python scripts/load_sample_data.py

# 6. Verify DB connection
python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://analytics_user:analytics_password@localhost:5432/analytics_db'); print(engine.connect())"
```

### Running Services (Daily Development)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Ctrl+C to stop
```

**Terminal 2 - Dashboard:**
```bash
cd dashboard
streamlit run app.py
# Press 'q' to stop
```

**Terminal 3 - Database Admin (optional):**
```bash
# Access at http://localhost:8080
# Server: postgres
# User: analytics_user
# Password: analytics_password
# Database: analytics_db
```

### Stopping Everything

```bash
# Stop services (Ctrl+C in each terminal)

# Stop & remove containers
docker-compose down

# Stop but keep data
docker-compose down -v
```

---

## 5. Common Development Tasks

### Add a New Python Dependency
```bash
poetry add pandas-new-library
poetry install
```

### Run Tests
```bash
# All tests
pytest

# Specific test file
pytest backend/tests/test_services/test_inventory_service.py

# With coverage
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html
```

### Format Code
```bash
# Format all files
black .

# Check formatting without changing
black --check .

# Lint
ruff check .
ruff check . --fix  # Auto-fix some issues
```

### Create Database Backup
```bash
docker-compose exec postgres pg_dump -U analytics_user analytics_db > backup.sql
```

### Restore Database from Backup
```bash
docker-compose exec -T postgres psql -U analytics_user analytics_db < backup.sql
```

### Fresh Database (Reset)
```bash
# Option 1: Full reset
docker-compose down -v  # Remove volumes (data)
docker-compose up -d postgres
python scripts/init_db.py
python scripts/load_sample_data.py

# Option 2: Just clear tables
python -c "
from sqlalchemy import text, create_engine
engine = create_engine('postgresql://analytics_user:analytics_password@localhost:5432/analytics_db')
with engine.begin() as conn:
    conn.execute(text('DROP TABLE IF EXISTS order_items CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS orders CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS products CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS inventory_snapshots CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS customers CASCADE'))
    conn.commit()
"
python scripts/init_db.py
```

---

## 6. Project Initialization Script

Create `scripts/init_project.sh` for one-command setup:

```bash
#!/bin/bash
set -e

echo "🚀 Initializing InventoryOS..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $python_version detected"

# Create .env if doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env created (update DATABASE_URL if needed)"
fi

# Create virtual environment
if [ ! -d venv ]; then
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install poetry
poetry install

# Start PostgreSQL
echo "🐘 Starting PostgreSQL..."
docker-compose up -d postgres
sleep 5  # Wait for DB to start

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py
python scripts/load_sample_data.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Terminal 1: cd backend && uvicorn main:app --reload"
echo "  2. Terminal 2: cd dashboard && streamlit run app.py"
echo ""
echo "Access:"
echo "  - Dashboard: http://localhost:8501"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - DB Admin: http://localhost:8080"
```

Run once with:
```bash
chmod +x scripts/init_project.sh
./scripts/init_project.sh
```

---

## 7. VS Code Extensions (Recommended)

Install these for optimal development:

```
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Ruff (charliermarsh.ruff)
- SQLTools (mtxr.sqltools)
- Streamlit (charliermarsh.streamlit)
- Thunder Client / REST Client (for API testing)
```

**.vscode/settings.json:**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["backend/tests", "models/tests"]
}
```

---

## 8. Troubleshooting

### PostgreSQL Connection Error
```
Error: could not connect to server: No such file or directory

Solution:
docker-compose up -d postgres
docker-compose logs postgres  # Check status
sleep 10  # Give it time to start
```

### Port Already in Use (8000, 8501, 5432)
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Poetry Lock Issues
```bash
rm poetry.lock
poetry install
```

### Module Not Found Error
```bash
# Ensure you're in the project root with venv activated
source venv/bin/activate
poetry install

# Or reinstall specific package
poetry add package-name
```

### Streamlit Cache Issues
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/

# Or run with no cache
streamlit run app.py --logger.level=debug
```

---

## 9. Using Claude Code

Once setup is complete, you can accelerate development:

### Option A: Initialize with Claude Code (Recommended)
```bash
# If Claude Code is installed
claude code . --instructions "Build the InventoryOS monorepo according to the PRD provided"
```

### Option B: Feed PRD to Claude Code
1. Copy the PRD content
2. Open Claude Code terminal in VS Code
3. Ask: "Build the full project structure from this PRD"
4. It will scaffold everything automatically

---

## 10. Git Workflow

### Initial Commit
```bash
git add .
git commit -m "chore: initial project structure"
git branch -M main
```

### Feature Development
```bash
# Create feature branch
git checkout -b feature/inventory-optimization

# Make changes, commit frequently
git add <files>
git commit -m "feat(inventory): add slow-mover detection"

# Push to origin
git push origin feature/inventory-optimization

# Create Pull Request (on GitHub/GitLab)
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
- `feat(api): add /forecasts endpoint`
- `fix(db): handle null COGS values`
- `docs(readme): add setup instructions`
- `test(inventory): add unit tests for EOQ`

---

## 11. Next Steps

1. ✅ Create folder & initialize Git
2. ✅ Copy files from this guide into the project
3. ✅ Run `scripts/init_project.sh` (or follow Step 4-6 manually)
4. ✅ Verify backend & dashboard run locally
5. 🎯 **Use Claude Code** to scaffold & build the full structure per the PRD

---

**You're all set!** The project is ready for Claude Code to build upon.
