"""Domain exceptions and standardized error response models for SANJEEVNI.

Ensures that errors are returned with machine-readable error codes and safe messages,
never leaking raw internal stack traces to clients.
"""
from typing import Any, Optional, Dict
from enum import Enum
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    INVALID_SENSOR_PACKET = "INVALID_SENSOR_PACKET"
    UNAUTHORIZED_DEVICE = "UNAUTHORIZED_DEVICE"
    DEVICE_NOT_FOUND = "DEVICE_NOT_FOUND"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SENSOR_ERROR = "SENSOR_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class SanjeevniException(HTTPException):
    """Base application exception for domain errors."""

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class InvalidSensorPacketException(SanjeevniException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            error_code=ErrorCode.INVALID_SENSOR_PACKET,
            message=message,
            details=details,
        )


class UnauthorizedDeviceException(SanjeevniException):
    def __init__(self, message: str = "Device is not authorized for this action"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED_DEVICE,
            message=message,
        )


class DeviceNotFoundException(SanjeevniException):
    def __init__(self, device_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.DEVICE_NOT_FOUND,
            message=f"Device with ID '{device_id}' was not found",
            details={"device_id": device_id},
        )


class InsufficientDataException(SanjeevniException):
    def __init__(self, message: str = "Insufficient sensor samples to compute metrics or inference"):
        super().__init__(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            error_code=ErrorCode.INSUFFICIENT_DATA,
            message=message,
        )


class ModelUnavailableException(SanjeevniException):
    def __init__(self, message: str = "Stress prediction ML model is not available"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.MODEL_UNAVAILABLE,
            message=message,
        )


class SensorErrorException(SanjeevniException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.SENSOR_ERROR,
            message=message,
            details=details,
        )


async def sanjeevni_exception_handler(request: Request, exc: SanjeevniException) -> JSONResponse:
    """Standardized handler for domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled exceptions to avoid leaking tracebacks."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "An internal server error occurred.",
            "details": {},
        },
    )
