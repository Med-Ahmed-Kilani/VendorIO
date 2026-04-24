"""pytest fixtures for backend tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.models.base import Base
from backend.models import Product, Order, OrderItem, Customer, InventorySnapshot
from backend.dependencies import get_db

SQLITE_URL = "sqlite://"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_product(db):
    p = Product(
        name="Test Coffee",
        category="Beverages",
        unit_price=15.99,
        cost_per_unit=5.00,
        current_stock=100,
        lead_time_days=7,
        reorder_point=20,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def sample_products(db):
    products = [
        Product(name="Coffee", category="Beverages", unit_price=15.99, cost_per_unit=5.00, current_stock=100, lead_time_days=7),
        Product(name="Tea", category="Beverages", unit_price=8.99, cost_per_unit=2.50, current_stock=5, lead_time_days=5),
        Product(name="Sugar", category="Food", unit_price=3.99, cost_per_unit=1.00, current_stock=200, lead_time_days=3),
    ]
    db.add_all(products)
    db.commit()
    for p in products:
        db.refresh(p)
    return products
