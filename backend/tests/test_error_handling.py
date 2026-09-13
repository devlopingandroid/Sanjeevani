"""Tests for centralized error handling and custom domain error codes."""
from fastapi import status


def test_device_not_found_error_payload(client):
    response = client.get("/api/v1/devices/NON_EXISTENT")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "DEVICE_NOT_FOUND"
    assert "not found" in data["message"]


def test_invalid_sensor_csv_error_payload(client):
    payload = {
        "device_id": "TEST_DEV",
        "csv_line": "invalid,short,csv",
    }
    response = client.post("/api/v1/sensors/ingest-csv", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "INVALID_SENSOR_PACKET"


def test_unauthorized_user_access(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "UNAUTHORIZED"
