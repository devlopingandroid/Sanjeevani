"""Stress prediction schemas adhering to the NO-MOCK-DATA policy."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.schemas.common import DataStatus


class StressInferenceRequest(BaseModel):
    device_id: str


class StressPredictionResponse(BaseModel):
    """Stress prediction output.

    If model is missing, returns data_status = MODEL_UNAVAILABLE.
    If samples are < 30s buffer, returns data_status = INSUFFICIENT_DATA.
    """
    device_id: str
    data_status: DataStatus
    stress_level: Optional[str] = None
    stress_score: Optional[float] = None
    confidence: Optional[float] = None
    predicted_at: Optional[datetime] = None
    model_status: str
    message: str
    features_used_count: int = 0
