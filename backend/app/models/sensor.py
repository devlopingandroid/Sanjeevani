"""Sensor data and sensor batch database models for Supabase PostgreSQL."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, synonym
from app.db.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False, index=True)

    # Sensor hardware timestamp (preserved from ESP32)
    sensor_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    # Backward compatibility synonym: timestamp maps to sensor_timestamp
    timestamp = synonym("sensor_timestamp")

    # Backend reception timestamp
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Optional sequence counter from firmware
    sequence_number = Column(Integer, nullable=True)

    # Ingestion transport: "SERIAL", "HTTP", "WIFI"
    transport = Column(String(20), server_default="HTTP", default="HTTP", nullable=False)

    # Evaluated signal quality: "GOOD", "FAIR", "POOR", "INVALID"
    quality = Column(String(20), server_default="GOOD", default="GOOD", nullable=False)

    # Optical PPG (MAX30102)
    ir = Column(Integer, nullable=False)
    red = Column(Integer, nullable=False)

    # Accelerometer (MPU6050)
    accel_x = Column(Integer, nullable=False)
    accel_y = Column(Integer, nullable=False)
    accel_z = Column(Integer, nullable=False)

    # Gyroscope (MPU6050)
    gyro_x = Column(Integer, nullable=False)
    gyro_y = Column(Integer, nullable=False)
    gyro_z = Column(Integer, nullable=False)

    # Skin Temperature (°F, MAX30205)
    temp_f = Column(Float, nullable=False)
    temperature = synonym("temp_f")

    # Galvanic Skin Response (GSR)
    gsr_raw = Column(Integer, nullable=False)
    gsr_voltage = Column(Float, nullable=False)

    device = relationship("Device", back_populates="sensor_records")

    __table_args__ = (
        Index("ix_sensor_data_device_sensor_ts", "device_id", "sensor_timestamp"),
        Index("ix_sensor_data_device_received_at", "device_id", "received_at"),
    )


class SensorBatch(Base):
    __tablename__ = "sensor_batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(64), unique=True, index=True, nullable=False)
    device_id = Column(String(100), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False, index=True)
    sample_count = Column(Integer, nullable=False)
    start_timestamp = Column(DateTime(timezone=True), nullable=False)
    end_timestamp = Column(DateTime(timezone=True), nullable=False)
    transport = Column(String(20), default="HTTP", nullable=False)
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
