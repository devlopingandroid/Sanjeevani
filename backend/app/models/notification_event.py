"""NotificationEvent database model for Sanjeevni Phase 6 Trusted Contact Notification Service."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    risk_event_id = Column(
        String(36),
        ForeignKey("risk_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trusted_contact_id = Column(
        String(36),
        ForeignKey("trusted_contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recipient_phone = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=False)  # twilio_sms | twilio_whatsapp | webhook | console
    status = Column(
        String(50), nullable=False
    )  # sent | failed | skipped_no_contact | skipped_no_consent | skipped_disabled | skipped_preference_mismatch | skipped_low_risk | skipped_duplicate
    notification_level = Column(String(50), nullable=True)
    risk_level = Column(String(20), nullable=False)
    attempt_count = Column(Integer, default=1, nullable=False)
    attempted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_category = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    risk_event = relationship("RiskEvent")
    user = relationship("User")
    trusted_contact = relationship("TrustedContact")

    __table_args__ = (
        Index("ix_notification_events_user_created", "user_id", "created_at"),
        Index("ix_notification_events_status", "status"),
    )
