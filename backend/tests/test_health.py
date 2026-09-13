"""Tests for health and readiness endpoints."""
from fastapi import status


def test_liveness_probe(client):
    response = client.get("/health/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert data["service"] == "sanjeevni-backend"


def test_readiness_probe(client):
    response = client.get("/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["dependencies"]["database"] == "connected"
    assert "ml_model" in data["dependencies"]


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "SANJEEVNI" in data["app"]
    assert "/docs" in data["docs"]
