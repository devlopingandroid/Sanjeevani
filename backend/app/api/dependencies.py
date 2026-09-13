"""FastAPI request dependencies."""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.device import Device
from app.services.device_service import DeviceService
from app.core.exceptions import (
    SanjeevniException,
    ErrorCode,
    DeviceNotFoundException,
    UnauthorizedDeviceException,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if not token:
        raise SanjeevniException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            message="Missing authentication credentials",
        )
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise SanjeevniException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            message="Invalid or expired authentication token",
        )
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise SanjeevniException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            message="User inactive or not found",
        )
    return user


def validate_device(device_id: str, db: Session = Depends(get_db)) -> Device:
    """Dependency verifying that the device ID exists or registers it."""
    device = DeviceService.get_or_create(db, device_id)
    return device
