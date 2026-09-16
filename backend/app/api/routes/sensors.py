"""Sensor data ingestion endpoints for real ESP32 wearable packets."""
from typing import Union
from fastapi import APIRouter, Depends, status, HTTPException
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
    summary="Get Latest Live Sensor Sample for Device",
    description="Returns the most recent validated real sensor reading directly from process memory.",
)
def get_latest_sensor_sample_by_device(device_id: str):
    from app.services.live_cache import live_sensor_cache
    return live_sensor_cache.get_latest(device_id)


@router.get(
    "/latest",
    summary="Get Latest Live Sensor Sample",
    description="Returns the most recent validated real sensor reading across any connected device.",
)
def get_latest_sensor_sample_any():
    from app.services.live_cache import live_sensor_cache
    return live_sensor_cache.get_latest(None)


@router.get(
    "/live/{device_id}",
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

