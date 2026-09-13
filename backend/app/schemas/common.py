"""Common schemas and explicit data status enumerations for SANJEEVNI."""
from enum import Enum
from typing import Generic, Optional, TypeVar, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")


class DataStatus(str, Enum):
    """Explicit states indicating real availability of physiological data.

    In accordance with the NO-MOCK-DATA rule, these states must be returned
    whenever real hardware readings are absent or incomplete.
    """
    REAL_DATA = "REAL_DATA"
    NO_DATA = "NO_DATA"
    DEVICE_DISCONNECTED = "DEVICE_DISCONNECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SENSOR_ERROR = "SENSOR_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"


class APIResponse(BaseModel, Generic[T]):
    """Standard generic API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    data_status: DataStatus = DataStatus.REAL_DATA


class ErrorResponse(BaseModel):
    """Standard structured error response."""
    success: bool = False
    error_code: str
    message: str
    details: Dict[str, Any] = {}
