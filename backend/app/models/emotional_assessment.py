"""EmotionalAssessment database model for Sanjeevni AI Phase 3."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.database import Base


class EmotionalAssessment(Base):
    __tablename__ = "emotional_assessments"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id = Column(
        String(36),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    emotion = Column(String(50), nullable=False, default="unknown")
    distress_level = Column(Integer, nullable=False, default=0)
    llm_suggested_risk_level = Column(String(20), nullable=False, default="normal")
    crisis_indicator = Column(Boolean, nullable=False, default=False)
    confidence = Column(Float, nullable=False, default=0.0)
    reason_category = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    conversation = relationship("Conversation")
    chat_message = relationship("ChatMessage")
    user = relationship("User")

    __table_args__ = (
        Index("ix_emotional_assessments_user_created", "user_id", "created_at"),
        Index("ix_emotional_assessments_msg_id", "message_id"),
    )
