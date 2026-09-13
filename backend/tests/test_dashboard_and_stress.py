"""Tests ensuring the absolute NO-MOCK-DATA policy is enforced across endpoints."""
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.schemas.common import DataStatus
from app.models.device import Device, DeviceStatus


def test_dashboard_no_devices_registered(client):
    """Verifies that with zero devices, NO_DATA is returned, NOT mock vitals."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data_status"] == DataStatus.NO_DATA.value
    assert data["vitals"] is None
    assert data["stress"] is None
    assert "Waiting" in data["message"]


def test_dashboard_device_disconnected(client, db_session):
    """Verifies that an old device without recent telemetry is reported as DISCONNECTED."""
    # Register device with last_seen 10 minutes ago
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    device = Device(
        device_id="ESP32_DISCONNECTED_TEST",
        status=DeviceStatus.CONNECTED,
        last_seen=old_time,
    )
    db_session.add(device)
    db_session.commit()

    response = client.get("/api/v1/dashboard/summary?device_id=ESP32_DISCONNECTED_TEST")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data_status"] == DataStatus.DEVICE_DISCONNECTED.value
    assert data["device_status"] == DeviceStatus.DISCONNECTED.value
    assert data["vitals"] is None
    assert data["stress"] is None


def test_dashboard_device_collecting_data(client):
    """Verifies that a newly active device reports INSUFFICIENT_DATA while building buffer."""
    # Send just 1 packet (not enough for full window)
    packet = {
        "device_id": "ESP32_BUFFERING_TEST",
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
    client.post("/api/v1/sensors/ingest", json=packet)

    response = client.get("/api/v1/dashboard/summary?device_id=ESP32_BUFFERING_TEST")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data_status"] == DataStatus.INSUFFICIENT_DATA.value


def test_stress_prediction_model_unavailable(client, monkeypatch):
    """When ML model file is not present, returns MODEL_UNAVAILABLE, never fakes stress."""
    from app.ml.model_loader import model_loader
    monkeypatch.setattr(model_loader, "_is_loaded", False)
    monkeypatch.setattr(model_loader, "_model", None)
    response = client.post(
        "/api/v1/stress/predict", json={"device_id": "ESP32_MODEL_TEST"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data_status"] == DataStatus.MODEL_UNAVAILABLE.value
    assert data["stress_level"] is None
    assert data["stress_score"] is None
    assert data["model_status"] == "MODEL_UNAVAILABLE"


def test_stress_latest_no_data(client):
    """When no stress history exists, returns NO_DATA."""
    response = client.get("/api/v1/stress/latest/ESP32_NONEXISTENT")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data_status"] == DataStatus.NO_DATA.value
    assert data["stress_level"] is None
