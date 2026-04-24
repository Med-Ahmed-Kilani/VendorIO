"""Tests for /api/v1/orders endpoints."""
from datetime import datetime
import pytest
from fastapi.testclient import TestClient


def test_list_orders_empty(client: TestClient):
    resp = client.get("/api/v1/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data


def test_create_order(client: TestClient, sample_product):
    payload = {
        "order_date": datetime.utcnow().isoformat(),
        "status": "completed",
        "total_amount": 31.98,
        "items": [
            {"product_id": sample_product.id, "quantity": 2, "unit_price": 15.99, "line_total": 31.98}
        ],
    }
    resp = client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "completed"
    assert len(data["items"]) == 1


def test_get_order_not_found(client: TestClient):
    resp = client.get("/api/v1/orders/99999")
    assert resp.status_code == 404


def test_create_and_retrieve_order(client: TestClient, sample_product):
    create = client.post("/api/v1/orders", json={
        "order_date": datetime.utcnow().isoformat(),
        "status": "completed",
        "items": [{"product_id": sample_product.id, "quantity": 1, "unit_price": 15.99}],
    })
    assert create.status_code == 201
    order_id = create.json()["id"]

    get_resp = client.get(f"/api/v1/orders/{order_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == order_id


def test_date_filter(client: TestClient):
    resp = client.get("/api/v1/orders", params={
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-31T23:59:59",
    })
    assert resp.status_code == 200
