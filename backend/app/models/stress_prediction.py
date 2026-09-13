"""Stress prediction database model."""
from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, Float, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.db.database import Base


class StressPrediction(Base):
    __tablename__ = "stress_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # ML Output
    stress_level = Column(String(50), nullable=False)  # "LOW", "MODERATE", "HIGH"
    stress_score = Column(Float, nullable=False)  # Real probability/score 0.0 - 100.0
    confidence = Column(Float, nullable=False)
    features_snapshot = Column(JSON, nullable=True)  # Snapshot of 44 extracted features

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    device = relationship("Device", back_populates="predictions")

    __table_args__ = (
        Index("ix_stress_predictions_device_timestamp", "device_id", "timestamp"),
    )
