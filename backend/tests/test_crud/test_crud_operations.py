"""Tests for generic CRUD operations."""
import pytest
from backend.crud.product import product as product_crud
from backend.crud.order import order as order_crud
from backend.schemas.product import ProductCreate, ProductUpdate
from backend.schemas.order import OrderCreate


def test_create_product(db):
    payload = ProductCreate(name="Widget", unit_price=9.99, current_stock=50)
    p = product_crud.create(db, obj_in=payload)
    assert p.id is not None
    assert p.name == "Widget"


def test_get_product(db, sample_product):
    p = product_crud.get(db, sample_product.id)
    assert p is not None
    assert p.id == sample_product.id


def test_update_product(db, sample_product):
    updated = product_crud.update(
        db, db_obj=sample_product, obj_in=ProductUpdate(current_stock=999)
    )
    assert updated.current_stock == 999


def test_soft_delete_product(db, sample_product):
    deleted = product_crud.soft_delete(db, product_id=sample_product.id)
    assert deleted.deleted_at is not None


def test_get_active_products(db, sample_products):
    active = product_crud.get_active(db)
    assert len(active) >= len(sample_products)
    assert all(p.deleted_at is None for p in active)


def test_get_categories(db, sample_products):
    categories = product_crud.get_categories(db)
    assert isinstance(categories, list)
    assert len(categories) > 0


def test_count_active(db, sample_products):
    count = product_crud.count_active(db)
    assert count >= len(sample_products)
