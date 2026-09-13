"""Device request and response schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.device import DeviceStatus


class DeviceCreate(BaseModel):
    device_id: str = Field(..., min_length=3, max_length=100, description="Hardware device ID / MAC address")
    name: Optional[str] = Field(None, max_length=100, description="Human-friendly device name")
    firmware_version: Optional[str] = Field(None, max_length=50)


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    firmware_version: Optional[str] = None


class DeviceStatusUpdate(BaseModel):
    status: DeviceStatus = Field(..., description="Target device status")


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    name: Optional[str] = None
    user_id: Optional[int] = None
    status: DeviceStatus
    last_seen: Optional[datetime] = None
    firmware_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
