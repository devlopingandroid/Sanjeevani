"""Tests for device lifecycle and status management."""
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.models.device import Device, DeviceStatus


def test_register_device(client):
    payload = {
        "device_id": "ESP32_NEW_DEVICE",
        "name": "Yash Smart Wristband",
        "firmware_version": "v1.0.4",
    }
    response = client.post("/api/v1/devices/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["device_id"] == "ESP32_NEW_DEVICE"
    assert data["status"] == DeviceStatus.REGISTERED.value
    assert data["last_seen"] is None


def test_get_device(client):
    # Register first
    client.post("/api/v1/devices/", json={"device_id": "ESP32_LOOKUP_TEST"})
    response = client.get("/api/v1/devices/ESP32_LOOKUP_TEST")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["device_id"] == "ESP32_LOOKUP_TEST"


def test_device_not_found(client):
    response = client.get("/api/v1/devices/NON_EXISTENT_DEVICE")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["error_code"] == "DEVICE_NOT_FOUND"


def test_device_status_transition_on_telemetry(client):
    # Register device
    client.post("/api/v1/devices/", json={"device_id": "ESP32_TRANSITION_TEST"})

    # Check status initially is REGISTERED
    r1 = client.get("/api/v1/devices/ESP32_TRANSITION_TEST")
    assert r1.json()["status"] == DeviceStatus.REGISTERED.value

    # Ingest a real packet
    packet = {
        "device_id": "ESP32_TRANSITION_TEST",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "IR": 27000,
        "RED": 18000,
        "Accel_X": 1000,
        "Accel_Y": 1000,
        "Accel_Z": 16000,
        "Gyro_X": 0,
        "Gyro_Y": 0,
        "Gyro_Z": 0,
        "Temp_F": 98.6,
        "GSR_Raw": 1800,
        "GSR_Voltage": 1.45,
    }
    r_ingest = client.post("/api/v1/sensors/ingest", json=packet)
    assert r_ingest.status_code == status.HTTP_201_CREATED

    # Verify device status is now dynamically evaluated as CONNECTED
    r2 = client.get("/api/v1/devices/ESP32_TRANSITION_TEST")
    assert r2.json()["status"] == DeviceStatus.CONNECTED.value
    assert r2.json()["last_seen"] is not None
