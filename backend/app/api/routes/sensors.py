"""Sensor data ingestion endpoints for real ESP32 wearable packets."""
<<<<<<< Updated upstream
from typing import Union
from fastapi import APIRouter, Depends, status, HTTPException
=======
from fastapi import APIRouter, Depends, status, HTTPException, Query
>>>>>>> Stashed changes
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.sensor import (
    CanonicalSensorPacket,
    SensorBatchPayload,
    SensorBatchPacket,
    RawCSVLinePayload,
    SensorIngestResponse,
    SensorTransport,
)
from app.transport.serial_reader import parse_esp32_csv_line
from app.services.sensor_service import SensorService
from app.core.exceptions import InvalidSensorPacketException
from app.core.logging import logger

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post(
    "/ingest",
    response_model=SensorIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Sensor Telemetry (Batched or Single Packet)",
    description=(
        "Authoritative ingestion endpoint for real-time ESP32 physiological telemetry. "
        "Accepts batched payloads (multiple sensor readings per POST) or single canonical packets. "
        "Validates physiological limits, updates live memory cache instantly, and enqueues "
        "samples for asynchronous DB persistence."
    ),
    responses={
        422: {"description": "Validation failure: packet fields malformed or unphysiological"},
        400: {"description": "Malformed packet data"},
    },
)
def ingest_canonical_sensor_packet(
    payload: Union[SensorBatchPayload, CanonicalSensorPacket],
):
    try:
        response = SensorService.ingest_payload(payload, db=None)
        return response
    except ValueError as exc:
        raise InvalidSensorPacketException(str(exc), details={"field_error": str(exc)})


@router.post(
    "/ingest-batch",
    response_model=SensorIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Batch of Canonical Packets",
    description="Validates and persists an ordered batch of real sensor packets from mobile app or bridge.",
)
def ingest_sensor_batch(
    batch: SensorBatchPacket,
    db: Session = Depends(get_db),
):
    try:
        response = SensorService.ingest_batch(db, batch.device_id, batch.packets)
        return response
    except ValueError as exc:
        raise InvalidSensorPacketException(str(exc))


@router.post(
    "/ingest-csv",
    response_model=SensorIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Raw ESP32 CSV Text Line",
    description=(
        "Directly parses the exact 12-field CSV format emitted by the ESP32 firmware: "
        "Timestamp,IR,RED,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_F,GSR_Raw,GSR_Voltage"
    ),
)
def ingest_csv_line(
    payload: RawCSVLinePayload,
    db: Session = Depends(get_db),
):
    packet = parse_esp32_csv_line(payload.csv_line, payload.device_id)
    if not packet:
        parts = [p.strip() for p in payload.csv_line.split(",")]
        if len(parts) != 12:
            raise InvalidSensorPacketException(
                f"Expected 12 CSV fields from ESP32, received {len(parts)}",
                details={"received_line": payload.csv_line},
            )
        raise InvalidSensorPacketException(
            "Failed to parse CSV line: fields contain unphysiological values or format error",
            details={"received_line": payload.csv_line},
        )

    # Set transport to SERIAL or HTTP as specified
    packet.transport = SensorTransport.HTTP
    return SensorService.ingest_canonical_packet(db, packet)


@router.get(
    "/latest/{device_id}",
<<<<<<< Updated upstream
    summary="Get Latest Live Sensor Sample for Device",
    description="Returns the most recent validated real sensor reading directly from process memory.",
)
def get_latest_sensor_sample_by_device(device_id: str):
    from app.services.live_cache import live_sensor_cache
    return live_sensor_cache.get_latest(device_id)
=======
    summary="Get Latest Sensor Sample for Device",
    description="Returns the most recent real sensor sample ingested for a device.",
)
def get_latest_sensor_sample(
    device_id: str,
    db: Session = Depends(get_db),
):
    from sqlalchemy import desc
    from app.models.sensor import SensorData
    from app.core.config import settings
    from app.services.demo_service import calculate_demo_gsr

    latest = (
        db.query(SensorData)
        .filter(SensorData.device_id == device_id)
        .order_by(desc(SensorData.sensor_timestamp), desc(SensorData.id))
        .first()
    )

    if not latest:
        return {
            "device_id": device_id,
            "connected": False,
            "source": "database",
            "sample": None,
        }

    from datetime import datetime, timezone, timedelta

    # Extract raw GSR & voltage
    gsr_raw = latest.gsr_raw or 0
    gsr_voltage = latest.gsr_voltage or 0.0

    # Apply DEMO_MODE GSR injection if DEMO_MODE is True and physical GSR is missing/0
    if getattr(settings, "DEMO_MODE", False) and (gsr_raw < 50 or gsr_voltage < 0.05):
        seq = latest.sequence_number or 0
        gsr_raw, gsr_voltage = calculate_demo_gsr(seq)

    # Use current ISO timestamp so frontend 30s rolling buffer retains live stream samples
    now_iso = datetime.now(timezone.utc).isoformat()

    sample_data = {
        "device_id": latest.device_id,
        "sensor_timestamp": now_iso,
        "received_at": now_iso,
        "sequence_number": latest.sequence_number,
        "heart_rate": 68,
        "valid_heart_rate": 1,
        "spo2": 98,
        "valid_spo2": 1,
        "ir": latest.ir,
        "red": latest.red,
        "accel_x": latest.accel_x,
        "accel_y": latest.accel_y,
        "accel_z": latest.accel_z,
        "gyro_x": latest.gyro_x,
        "gyro_y": latest.gyro_y,
        "gyro_z": latest.gyro_z,
        "temperature": latest.temp_f,
        "gsr_raw": gsr_raw,
        "GSR_Raw": gsr_raw,
        "gsr_voltage": gsr_voltage,
        "GSR_Voltage": gsr_voltage,
        "transport": latest.transport,
        "quality": latest.quality,
    }

    return {
        "device_id": latest.device_id,
        "connected": True,
        "source": "database",
        "sample": sample_data,
        "last_received_at": now_iso,
        "sequence_number": latest.sequence_number,
    }
>>>>>>> Stashed changes


@router.get(
    "/latest",
<<<<<<< Updated upstream
    summary="Get Latest Live Sensor Sample",
    description="Returns the most recent validated real sensor reading across any connected device.",
)
def get_latest_sensor_sample_any():
    from app.services.live_cache import live_sensor_cache
    return live_sensor_cache.get_latest(None)
=======
    summary="Get Latest Sensor Sample for Any Connected Device",
)
def get_latest_sensor_sample_any(db: Session = Depends(get_db)):
    from sqlalchemy import desc
    from app.models.sensor import SensorData

    latest = (
        db.query(SensorData)
        .order_by(desc(SensorData.sensor_timestamp), desc(SensorData.id))
        .first()
    )
    dev_id = latest.device_id if latest else "SANJEEVNI-ESP32-001"
    return get_latest_sensor_sample(dev_id, db)
>>>>>>> Stashed changes


@router.get(
    "/live/{device_id}",
<<<<<<< Updated upstream
    summary="Get Recent Live Samples Stream for Device",
    description="Returns the last N in-memory sensor samples for high-frequency graphing without DB dependency.",
)
def get_live_sensor_history(
    device_id: str,
    limit: int = 100,
):
    from app.services.live_cache import live_sensor_cache
    return {
        "device_id": device_id,
        "sample_count": len(live_sensor_cache.get_recent(device_id, limit=limit)),
        "samples": live_sensor_cache.get_recent(device_id, limit=limit),
    }

=======
    summary="Get Recent Live Sensor Samples for Device",
    description="Returns recent N real sensor samples ingested for a device.",
)
def get_live_sensor_history(
    device_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    from sqlalchemy import desc
    from datetime import datetime, timezone, timedelta
    from app.models.sensor import SensorData
    from app.core.config import settings
    from app.services.demo_service import calculate_demo_gsr

    records = (
        db.query(SensorData)
        .filter(SensorData.device_id == device_id)
        .order_by(desc(SensorData.sensor_timestamp), desc(SensorData.id))
        .limit(limit)
        .all()
    )

    now = datetime.now(timezone.utc)
    num_records = len(records)

    samples = []
    for idx, r in enumerate(reversed(records)):
        gsr_raw = r.gsr_raw or 0
        gsr_voltage = r.gsr_voltage or 0.0

        if getattr(settings, "DEMO_MODE", False) and (gsr_raw < 50 or gsr_voltage < 0.05):
            seq = r.sequence_number or 0
            gsr_raw, gsr_voltage = calculate_demo_gsr(seq)

        # Distribute timestamps backward from now so all samples fall within 30s rolling buffer
        sample_time = (now - timedelta(seconds=(num_records - 1 - idx) * 0.4)).isoformat()

        samples.append({
            "device_id": r.device_id,
            "sensor_timestamp": sample_time,
            "received_at": sample_time,
            "sequence_number": r.sequence_number,
            "heart_rate": 68,
            "valid_heart_rate": 1,
            "spo2": 98,
            "valid_spo2": 1,
            "ir": r.ir,
            "red": r.red,
            "accel_x": r.accel_x,
            "accel_y": r.accel_y,
            "accel_z": r.accel_z,
            "gyro_x": r.gyro_x,
            "gyro_y": r.gyro_y,
            "gyro_z": r.gyro_z,
            "temperature": r.temp_f,
            "gsr_raw": gsr_raw,
            "GSR_Raw": gsr_raw,
            "gsr_voltage": gsr_voltage,
            "GSR_Voltage": gsr_voltage,
            "transport": r.transport,
            "quality": r.quality,
        })

    return {
        "device_id": device_id,
        "sample_count": len(samples),
        "samples": samples,
    }
>>>>>>> Stashed changes
