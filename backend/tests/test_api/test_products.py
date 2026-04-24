"""Tests for /api/v1/products endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_list_products_empty(client: TestClient):
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data


def test_create_product(client: TestClient):
    payload = {
        "name": "Espresso Beans",
        "category": "Beverages",
        "unit_price": 22.50,
        "cost_per_unit": 8.00,
        "current_stock": 150,
        "lead_time_days": 7,
    }
    resp = client.post("/api/v1/products", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Espresso Beans"
    assert data["id"] is not None


def test_get_product(client: TestClient, sample_product):
    resp = client.get(f"/api/v1/products/{sample_product.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_product.id


def test_get_product_not_found(client: TestClient):
    resp = client.get("/api/v1/products/99999")
    assert resp.status_code == 404


def test_update_product(client: TestClient, sample_product):
    resp = client.put(
        f"/api/v1/products/{sample_product.id}",
        json={"current_stock": 50},
    )
    assert resp.status_code == 200
    assert resp.json()["current_stock"] == 50


def test_delete_product(client: TestClient, sample_product):
    resp = client.delete(f"/api/v1/products/{sample_product.id}")
    assert resp.status_code == 204
    # Verify soft-deleted product not returned
    resp = client.get(f"/api/v1/products/{sample_product.id}")
    assert resp.status_code == 404


def test_filter_by_category(client: TestClient, sample_products):
    resp = client.get("/api/v1/products", params={"category": "Beverages"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(p["category"] == "Beverages" for p in data["data"])
