"""RiskEvent database model for Sanjeevni Phase 4 Deterministic Distress Risk Engine."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessment_id = Column(
        String(36),
        ForeignKey("emotional_assessments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    risk_level = Column(String(20), nullable=False)  # AUTHORITATIVE: NORMAL | ELEVATED | HIGH | CRITICAL
    reason_category = Column(String(100), nullable=True)
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    action_taken = Column(String(100), nullable=True)
    trusted_contact_notified = Column(Boolean, nullable=False, default=False)
    notification_status = Column(
        String(50), nullable=False, default="no_trusted_contact_configured"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = relationship("User")
    conversation = relationship("Conversation")
    assessment = relationship("EmotionalAssessment")

    __table_args__ = (
        Index("ix_risk_events_user_created", "user_id", "created_at"),
    )
