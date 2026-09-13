"""Device management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceStatusUpdate
from app.services.device_service import DeviceService
from app.api.dependencies import get_current_user_optional
from app.models.user import User
from app.core.exceptions import DeviceNotFoundException

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Device",
    description="Registers a new ESP32 wearable hardware identifier.",
)
def register_device(
    device_in: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    return DeviceService.register_device(db, device_in, user_id=user_id)


@router.get(
    "/",
    response_model=List[DeviceResponse],
    summary="List Devices",
    description="Lists all registered devices and dynamically evaluates connection state.",
)
def list_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    devices = DeviceService.list_devices(db, skip, limit)
    # Dynamically refresh status based on last_seen
    return [DeviceService.refresh_status(db, d) for d in devices]


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get Device Details",
    description="Retrieves a device and its live evaluated connectivity status.",
)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
):
    device = DeviceService.get_by_device_id(db, device_id)
    if not device:
        raise DeviceNotFoundException(device_id)
    return DeviceService.refresh_status(db, device)


@router.patch(
    "/{device_id}/status",
    response_model=DeviceResponse,
    summary="Update Device Status",
    description="Updates explicit hardware status (e.g. CONNECTING, ERROR).",
)
def update_device_status(
    device_id: str,
    status_in: DeviceStatusUpdate,
    db: Session = Depends(get_db),
):
    device = DeviceService.get_by_device_id(db, device_id)
    if not device:
        raise DeviceNotFoundException(device_id)
    device.status = status_in.status
    db.commit()
    db.refresh(device)
    return device
