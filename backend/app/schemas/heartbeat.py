"""Device heartbeat request and response schemas."""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class DeviceHeartbeatRequest(BaseModel):
    device_id: str = Field(..., min_length=3, max_length=100, description="Hardware device ID / MAC address")
    firmware_version: Optional[str] = Field("0.1.0", max_length=50, description="ESP32 firmware version")
    transport: str = Field("wifi", max_length=20, description="Transport medium (wifi, bluetooth, serial)")
    timestamp: Optional[str] = Field(None, description="ISO format string or timestamp from ESP32")


class DeviceHeartbeatResponse(BaseModel):
    status: str = Field("acknowledged", description="Heartbeat acknowledgement status")
    device_id: str
    connection_status: str = Field(..., description="Evaluated connection status: CONNECTED")
    last_seen: datetime
    firmware_version: Optional[str] = None
    transport: Optional[str] = None
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}
