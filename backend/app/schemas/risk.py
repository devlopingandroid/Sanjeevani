"""Pydantic schemas for Phase 4 Deterministic Distress Risk Engine."""
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuthoritativeRiskLevel(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    conversation_id: str
    assessment_id: Optional[str] = None
    risk_level: AuthoritativeRiskLevel
    reason_category: Optional[str] = None
    detected_at: datetime
    action_taken: Optional[str] = None
    trusted_contact_notified: bool
    notification_status: str
    created_at: datetime
