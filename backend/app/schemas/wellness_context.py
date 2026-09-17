"""Pydantic schemas for Phase 7 Multimodal Wellness Context."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MultimodalWellnessResponse(BaseModel):
    """Schema for multimodal wellness context evaluation response."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    conversation_id: Optional[str] = None
    device_id: Optional[str] = None

    # Constituent Signals (Neutral, non-clinical labels)
    physiological_stress_level: Optional[str] = None  # "BASELINE", "LOW", "MODERATE", "HIGH", or None
    physiological_stress_score: Optional[float] = None  # 0.0 - 100.0
    conversational_risk_level: Optional[str] = None  # "NORMAL", "ELEVATED", "HIGH", "CRITICAL", or None
    crisis_indicator: bool = False

    # Multimodal Evaluation Result
    wellness_concern_level: str  # "normal_wellness", "elevated_concern", "high_concern", "critical_concern"
    rule_applied: str  # "CRISIS_LANGUAGE_OVERRIDE", "SENSOR_HIGH_CAPPED_AT_ELEVATED", "BOTH_SIGNALS_AGREE", "ROUTINE_MONITORING"
    explanation: str
    evaluated_at: datetime
