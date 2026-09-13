"""Historical vitals and sensor telemetry query endpoints."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.database import get_db
from app.models.sensor import SensorData
from app.models.processed_metrics import ProcessedMetrics
from app.models.stress_prediction import StressPrediction
from app.schemas.dashboard import VitalsSnapshot

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "/vitals/{device_id}",
    summary="Historical Vitals",
    description="Returns recorded vitals from real sensor streams for a device.",
)
def get_vitals_history(
    device_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    records = (
        db.query(ProcessedMetrics)
        .filter(ProcessedMetrics.device_id == device_id)
        .order_by(desc(ProcessedMetrics.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {
            "timestamp": r.timestamp,
            "heart_rate_bpm": r.heart_rate_bpm,
            "hrv_rmssd_ms": r.hrv_rmssd_ms,
            "temperature_f": r.temperature_f,
            "skin_conductance_us": r.skin_conductance_us,
            "motion_magnitude": r.motion_magnitude,
        }
        for r in records
    ]


@router.get(
    "/raw/{device_id}",
    summary="Historical Raw Sensor Samples",
    description="Returns real raw 12-channel sensor recordings for an ESP32 device.",
)
def get_raw_history(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    records = (
        db.query(SensorData)
        .filter(SensorData.device_id == device_id)
        .order_by(desc(SensorData.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {
            "timestamp": r.timestamp,
            "ir": r.ir,
            "red": r.red,
            "accel_x": r.accel_x,
            "accel_y": r.accel_y,
            "accel_z": r.accel_z,
            "gyro_x": r.gyro_x,
            "gyro_y": r.gyro_y,
            "gyro_z": r.gyro_z,
            "temp_f": r.temp_f,
            "gsr_raw": r.gsr_raw,
            "gsr_voltage": r.gsr_voltage,
        }
        for r in records
    ]
