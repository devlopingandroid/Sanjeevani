"""Dashboard schemas adhering to the strict NO-MOCK-DATA policy."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.device import DeviceStatus
from app.schemas.common import DataStatus


class VitalsSnapshot(BaseModel):
    heart_rate_bpm: Optional[float] = None
    hrv_rmssd_ms: Optional[float] = None
    temperature_f: Optional[float] = None
    skin_conductance_us: Optional[float] = None
    motion_magnitude: Optional[float] = None
    last_updated: Optional[datetime] = None


class StressSnapshot(BaseModel):
    stress_level: Optional[str] = None  # "LOW", "MODERATE", "HIGH"
    stress_score: Optional[float] = None  # 0.0 - 100.0
    confidence: Optional[float] = None
    predicted_at: Optional[datetime] = None


class DashboardSummaryResponse(BaseModel):
    """Authoritative dashboard summary.

    When no real sensor stream is available, vitals and stress are explicitly null,
    and data_status is set to NO_DATA, DEVICE_DISCONNECTED, or INSUFFICIENT_DATA.
    """
    device_id: Optional[str] = None
    device_status: DeviceStatus = DeviceStatus.NO_DATA
    data_status: DataStatus = DataStatus.NO_DATA
    last_seen: Optional[datetime] = None
    vitals: Optional[VitalsSnapshot] = None
    stress: Optional[StressSnapshot] = None
    message: str = "Waiting for real wearable sensor data..."
