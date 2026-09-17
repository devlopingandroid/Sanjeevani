"""Pydantic schemas for Phase 5 Trusted Contact and Consent."""
import re
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class NotificationLevel(str, Enum):
    HIGH_AND_CRITICAL = "high_and_critical"
    CRITICAL_ONLY = "critical_only"


PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


class TrustedContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., min_length=7, max_length=50)
    relationship: Optional[str] = Field(None, max_length=100)
    enabled: bool = True
    consent_given: bool = Field(..., description="Explicit consent mandatory")
    notification_level: NotificationLevel = NotificationLevel.CRITICAL_ONLY

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Name cannot be empty or blank")
        return s

    @field_validator("phone_number")
    def validate_phone(cls, v: str) -> str:
        s = v.strip()
        if not PHONE_REGEX.match(s):
            raise ValueError("Invalid phone number format. Provide a valid international or local phone number.")
        return s

    @field_validator("consent_given")
    def validate_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Explicit consent is mandatory before adding a trusted contact.")
        return v


class TrustedContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=7, max_length=50)
    relationship: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    consent_given: Optional[bool] = None
    notification_level: Optional[NotificationLevel] = None

    @field_validator("name")
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("Name cannot be empty or blank")
            return s
        return v

    @field_validator("phone_number")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not PHONE_REGEX.match(s):
                raise ValueError("Invalid phone number format.")
            return s
        return v


class TrustedContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    name: str
    phone_number: str
    relationship: Optional[str] = None
    enabled: bool
    consent_given: bool
    notification_level: NotificationLevel
    created_at: datetime
    updated_at: datetime
