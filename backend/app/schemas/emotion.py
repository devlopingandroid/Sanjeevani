"""Pydantic schemas for Emotion and Distress Analysis (Phase 3)."""
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EmotionType(str, Enum):
    NEUTRAL = "neutral"
    STRESSED = "stressed"
    ANXIOUS_DISTRESS = "anxious_distress"
    LOW_MOOD = "low_mood"
    POSITIVE = "positive"
    OVERWHELMED = "overwhelmed"
    UNKNOWN = "unknown"


class DistressLevel(int, Enum):
    NONE_MINIMAL = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3


class LLMSuggestedRiskLevel(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class EmotionalAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    message_id: str
    user_id: int
    emotion: EmotionType
    distress_level: int = Field(..., ge=0, le=3)
    llm_suggested_risk_level: LLMSuggestedRiskLevel
    crisis_indicator: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason_category: Optional[str] = None
    created_at: datetime



class EmotionAnalysisLLMOutput(BaseModel):
    """Raw structured output expected from LLM emotion analysis call."""
    emotion: EmotionType = EmotionType.UNKNOWN
    distress_level: int = 0
    llm_suggested_risk_level: LLMSuggestedRiskLevel = LLMSuggestedRiskLevel.NORMAL
    crisis_indicator: bool = False
    confidence: float = 0.0
    reason_category: Optional[str] = None

    @field_validator("confidence", mode="before")
    def clamp_confidence(cls, v):
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0

    @field_validator("distress_level", mode="before")
    def clamp_distress(cls, v):
        try:
            val = int(v)
            return max(0, min(3, val))
        except (ValueError, TypeError):
            return 0
