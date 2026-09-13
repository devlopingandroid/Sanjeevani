"""Phase 2 tests for canonical sensor ingestion, validation, quality grading, and serial parser."""
import math
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.schemas.sensor import (
    CanonicalSensorPacket,
    SensorQuality,
    SensorTransport,
)
from app.transport.serial_reader import parse_esp32_csv_line
from app.models.device import Device, DeviceStatus
from app.models.sensor import SensorData


def get_canonical_packet(device_id: str = "ESP32_CANONICAL_TEST"):
    """Deterministic test packet."""
    return {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence_number": 100,
        "IR": 27156,
        "RED": 18003,
        "Accel_X": 1056,
        "Accel_Y": 1152,
        "Accel_Z": 16428,
        "Gyro_X": -136,
        "Gyro_Y": 221,
        "Gyro_Z": 110,
        "Temp_F": 91.58,
        "GSR_Raw": 1911,
        "GSR_Voltage": 1.54,
        "transport": "HTTP",
    }


def test_ingest_canonical_packet_success(client, db_session):
    packet = get_canonical_packet("DEV_CANONICAL_01")
    response = client.post("/api/v1/sensors/ingest", json=packet)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["accepted"] is True
    assert data["device_id"] == "DEV_CANONICAL_01"
    assert data["quality"] == SensorQuality.GOOD.value
    assert data["is_duplicate"] is False
    assert data["is_out_of_order"] is False
    assert "received_at" in data
    assert "sensor_timestamp" in data

    # Verify database persistence
    db_rec = (
        db_session.query(SensorData)
        .filter(SensorData.device_id == "DEV_CANONICAL_01")
        .first()
    )
    assert db_rec is not None
    assert db_rec.ir == 27156
    assert db_rec.red == 18003
    assert db_rec.temp_f == 91.58
    assert db_rec.gsr_voltage == 1.54
    assert db_rec.transport == "HTTP"
    assert db_rec.quality == "GOOD"
    assert db_rec.sensor_timestamp is not None
    assert db_rec.received_at is not None


def test_reject_nan_values(client):
    import pytest
    from pydantic import ValidationError
    packet_dict = get_canonical_packet()
    packet_dict["Temp_F"] = float("nan")
    with pytest.raises(ValidationError):
        CanonicalSensorPacket(**packet_dict)

    # Also test sending NaN string over HTTP
    raw_json = '{"device_id": "TEST", "timestamp": "2026-09-13T10:00:00Z", "IR": 20000, "RED": 20000, "Accel_X": 0, "Accel_Y": 0, "Accel_Z": 16000, "Gyro_X": 0, "Gyro_Y": 0, "Gyro_Z": 0, "Temp_F": "NaN", "GSR_Raw": 1000, "GSR_Voltage": 1.5}'
    r = client.post("/api/v1/sensors/ingest", content=raw_json, headers={"Content-Type": "application/json"})
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reject_infinity_values(client):
    import pytest
    from pydantic import ValidationError
    packet_dict = get_canonical_packet()
    packet_dict["GSR_Voltage"] = float("inf")
    with pytest.raises(ValidationError):
        CanonicalSensorPacket(**packet_dict)


def test_quality_grading_fair(client):
    # Weak optical count (between 1000 and 5000)
    packet = get_canonical_packet("DEV_FAIR_TEST")
    packet["IR"] = 2500
    packet["RED"] = 2200
    response = client.post("/api/v1/sensors/ingest", json=packet)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["quality"] == SensorQuality.FAIR.value


def test_quality_grading_poor_leadoff(client):
    # IR < 1000 indicates sensor lead-off
    packet = get_canonical_packet("DEV_POOR_TEST")
    packet["IR"] = 450
    packet["RED"] = 400
    response = client.post("/api/v1/sensors/ingest", json=packet)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["quality"] == SensorQuality.POOR.value


def test_duplicate_packet_detection(client, db_session):
    packet = get_canonical_packet("DEV_DUP_TEST")
    packet["sequence_number"] = 42

    # First ingestion -> Accepted
    r1 = client.post("/api/v1/sensors/ingest", json=packet)
    assert r1.status_code == status.HTTP_201_CREATED
    assert r1.json()["accepted"] is True
    assert r1.json()["is_duplicate"] is False

    # Second ingestion with same device_id and sequence_number -> Flagged Duplicate
    r2 = client.post("/api/v1/sensors/ingest", json=packet)
    assert r2.status_code == status.HTTP_201_CREATED
    data2 = r2.json()
    assert data2["accepted"] is False
    assert data2["is_duplicate"] is True

    # Check only 1 record exists in DB
    count = db_session.query(SensorData).filter(SensorData.device_id == "DEV_DUP_TEST").count()
    assert count == 1


def test_out_of_order_packet_detection(client):
    device_id = "DEV_OUT_OF_ORDER_TEST"
    t_now = datetime.now(timezone.utc)

    # Ingest newer packet
    p_newer = get_canonical_packet(device_id)
    p_newer["timestamp"] = t_now.isoformat()
    p_newer["sequence_number"] = 20
    r1 = client.post("/api/v1/sensors/ingest", json=p_newer)
    assert r1.status_code == status.HTTP_201_CREATED
    assert r1.json()["is_out_of_order"] is False

    # Ingest older packet (arrived late)
    p_older = get_canonical_packet(device_id)
    p_older["timestamp"] = (t_now - timedelta(seconds=2)).isoformat()
    p_older["sequence_number"] = 19
    r2 = client.post("/api/v1/sensors/ingest", json=p_older)
    assert r2.status_code == status.HTTP_201_CREATED
    data2 = r2.json()
    assert data2["accepted"] is True
    assert data2["is_out_of_order"] is True


def test_device_telemetry_counters(client, db_session):
    device_id = "DEV_METRICS_TEST"
    packet = get_canonical_packet(device_id)
    packet["transport"] = "SERIAL"

    client.post("/api/v1/sensors/ingest", json=packet)

    dev = db_session.query(Device).filter(Device.device_id == device_id).first()
    assert dev is not None
    assert dev.status == DeviceStatus.CONNECTED
    assert dev.last_transport == "SERIAL"
    assert dev.total_packets_received >= 1
    assert dev.total_packets_accepted >= 1
    assert dev.last_valid_packet_at is not None


def test_serial_csv_parser_valid():
    now_str = datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S.120")
    csv_line = f"{now_str},27156,18003,1056,1152,16428,-136,221,110,91.58,1911,1.54"
    packet = parse_esp32_csv_line(csv_line, "SERIAL_ESP32_01")
    assert packet is not None
    assert packet.device_id == "SERIAL_ESP32_01"
    assert packet.ir == 27156
    assert packet.red == 18003
    assert packet.temperature == 91.58
    assert packet.transport == SensorTransport.SERIAL
    assert packet.quality == SensorQuality.GOOD


def test_serial_csv_parser_header_skip():
    header_line = "Timestamp,IR,RED,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_F,GSR_Raw,GSR_Voltage"
    packet = parse_esp32_csv_line(header_line, "SERIAL_ESP32_01")
    assert packet is None


def test_serial_csv_parser_malformed_columns():
    malformed_line = "13-09-2026 15:30:00,27156,18003"
    packet = parse_esp32_csv_line(malformed_line, "SERIAL_ESP32_01")
    assert packet is None


def test_serial_csv_parser_unphysiological_rejected():
    now_str = datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S.120")
    # Negative IR count is invalid
    bad_line = f"{now_str},-50,18003,1056,1152,16428,-136,221,110,91.58,1911,1.54"
    packet = parse_esp32_csv_line(bad_line, "SERIAL_ESP32_01")
    assert packet is None
