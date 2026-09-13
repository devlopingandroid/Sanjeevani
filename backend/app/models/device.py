"""Device database model and status enumeration for Supabase PostgreSQL."""
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.base import TimestampMixin


class DeviceStatus(str, Enum):
    REGISTERED = "REGISTERED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    NO_DATA = "NO_DATA"
    STALE = "STALE"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.REGISTERED, nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    firmware_version = Column(String(50), nullable=True)

    # Ingestion & Telemetry Observability Metrics
    last_packet_received_at = Column(DateTime(timezone=True), nullable=True)
    last_valid_packet_at = Column(DateTime(timezone=True), nullable=True)
    last_transport = Column(String(20), nullable=True)
    total_packets_received = Column(Integer, server_default="0", default=0, nullable=False)
    total_packets_accepted = Column(Integer, server_default="0", default=0, nullable=False)
    total_packets_rejected = Column(Integer, server_default="0", default=0, nullable=False)

    user = relationship("User", back_populates="devices")
    sensor_records = relationship("SensorData", back_populates="device", cascade="all, delete-orphan")
    metrics = relationship("ProcessedMetrics", back_populates="device", cascade="all, delete-orphan")
    predictions = relationship("StressPrediction", back_populates="device", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_devices_user_id_status", "user_id", "status"),
    )
