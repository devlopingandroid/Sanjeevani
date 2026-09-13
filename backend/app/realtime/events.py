"""WebSocket event types and schemas."""
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel


class RealtimeEventType(str, Enum):
    SENSOR_PACKET = "SENSOR_PACKET"
    VITALS_UPDATE = "VITALS_UPDATE"
    STRESS_ALERT = "STRESS_ALERT"
    DEVICE_STATUS_CHANGE = "DEVICE_STATUS_CHANGE"


class RealtimeEvent(BaseModel):
    event_type: RealtimeEventType
    device_id: str
    payload: Dict[str, Any]
