"""Stress prediction schemas adhering to the NO-MOCK-DATA policy."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import DataStatus


class StressInferenceRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")


class StressPredictionResponse(BaseModel):
    """Stress prediction output.

    If model is missing, returns data_status = MODEL_UNAVAILABLE.
    If samples are < 30s buffer, returns data_status = INSUFFICIENT_DATA.
    If sensor quality is poor (lead-off/saturation), returns data_status = SENSOR_ERROR.
    """
    device_id: str
    data_status: DataStatus
    stress_level: Optional[str] = None  # "BASELINE" or "STRESS"
    stress_score: Optional[float] = None  # Continuous score (0.0 - 100.0)
    raw_probability: Optional[float] = None  # Raw model probability [0.0 - 1.0]
    confidence: Optional[float] = None
    predicted_at: Optional[datetime] = None
    model_status: str
    message: str
    features_used_count: int = 0
    features_snapshot: Optional[Dict[str, float]] = None
