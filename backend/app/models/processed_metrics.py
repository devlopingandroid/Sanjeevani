"""Processed physiological metrics database model."""
from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, Float, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base


class ProcessedMetrics(Base):
    __tablename__ = "processed_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Vitals derived from real sensor signals
    heart_rate_bpm = Column(Float, nullable=True)
    hrv_rmssd_ms = Column(Float, nullable=True)
    hrv_sdnn_ms = Column(Float, nullable=True)
    temperature_f = Column(Float, nullable=True)
    skin_conductance_us = Column(Float, nullable=True)
    motion_magnitude = Column(Float, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    device = relationship("Device", back_populates="metrics")

    __table_args__ = (
        Index("ix_processed_metrics_device_timestamp", "device_id", "timestamp"),
    )
