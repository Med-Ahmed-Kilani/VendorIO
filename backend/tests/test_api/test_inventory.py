"""Tests for /api/v1/inventory endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_inventory_status_empty(client: TestClient):
    resp = client.get("/api/v1/inventory/status")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_product_health_not_found(client: TestClient):
    resp = client.get("/api/v1/inventory/99999/health")
    assert resp.status_code == 404


def test_product_health(client: TestClient, sample_product):
    resp = client.get(f"/api/v1/inventory/{sample_product.id}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == sample_product.id
    assert "current_stock" in data
    assert "status" in data


def test_inventory_sync(client: TestClient, sample_product):
    resp = client.post("/api/v1/inventory/sync")
    assert resp.status_code == 200
    data = resp.json()
    assert "synced" in data
    assert data["synced"] >= 1
