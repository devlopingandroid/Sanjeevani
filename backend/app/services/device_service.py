"""Device lifecycle, status, and telemetry tracking service."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.device import Device, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.config import settings
from app.core.exceptions import DeviceNotFoundException
from app.core.logging import logger


class DeviceService:

    @staticmethod
    def get_by_device_id(db: Session, device_id: str) -> Optional[Device]:
        return db.query(Device).filter(Device.device_id == device_id).first()

    @staticmethod
    def get_or_create(db: Session, device_id: str, name: Optional[str] = None) -> Device:
        """Retrieves an existing device or registers a new one in REGISTERED state."""
        device = DeviceService.get_by_device_id(db, device_id)
        if not device:
            device = Device(
                device_id=device_id,
                name=name or f"Wearable-{device_id[-4:] if len(device_id) >= 4 else device_id}",
                status=DeviceStatus.REGISTERED,
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            logger.info(f"Registered new wearable device: {device_id} [Status: REGISTERED]")
        return device

    @staticmethod
    def register_device(db: Session, obj_in: DeviceCreate, user_id: Optional[int] = None) -> Device:
        existing = DeviceService.get_by_device_id(db, obj_in.device_id)
        if existing:
            if user_id and not existing.user_id:
                existing.user_id = user_id
                db.commit()
                db.refresh(existing)
            return existing

        device = Device(
            device_id=obj_in.device_id,
            name=obj_in.name,
            firmware_version=obj_in.firmware_version,
            user_id=user_id,
            status=DeviceStatus.REGISTERED,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        logger.info(f"Device registered: {obj_in.device_id}")
        return device

    @staticmethod
    def list_devices(db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
        return db.query(Device).offset(skip).limit(limit).all()

    @staticmethod
    def update_heartbeat(
        db: Session,
        device_id: str,
        transport: str = "HTTP",
        is_valid: bool = True,
    ) -> Device:
        """Called when real telemetry arrives.

        Transitions device status to CONNECTED, updates last_seen and counters.
        """
        device = DeviceService.get_or_create(db, device_id)
        now = datetime.now(timezone.utc)
        device.last_seen = now
        device.last_packet_received_at = now
        device.last_transport = transport
        device.total_packets_received = (device.total_packets_received or 0) + 1

        if is_valid:
            device.last_valid_packet_at = now
            device.status = DeviceStatus.CONNECTED
            device.total_packets_accepted = (device.total_packets_accepted or 0) + 1
        else:
            device.total_packets_rejected = (device.total_packets_rejected or 0) + 1

        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def evaluate_device_status(device: Device) -> DeviceStatus:
        """Dynamically evaluates device status based on elapsed time since last_seen."""
        if not device.last_seen:
            return DeviceStatus.REGISTERED

        now = datetime.now(timezone.utc)
        last_seen = device.last_seen
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        elapsed_seconds = (now - last_seen).total_seconds()

        if elapsed_seconds > settings.DEVICE_DISCONNECT_TIMEOUT_SECONDS:
            return DeviceStatus.DISCONNECTED
        elif elapsed_seconds > settings.DEVICE_HEARTBEAT_TIMEOUT_SECONDS:
            return DeviceStatus.STALE
        return DeviceStatus.CONNECTED

    @staticmethod
    def refresh_status(db: Session, device: Device) -> Device:
        computed_status = DeviceService.evaluate_device_status(device)
        if device.status != computed_status:
            device.status = computed_status
            db.commit()
            db.refresh(device)
        return device
