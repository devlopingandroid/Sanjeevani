"""TrustedContact database model for Sanjeevni Phase 5."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship as sa_relationship

from app.db.database import Base
from app.models.base import TimestampMixin


class TrustedContact(Base, TimestampMixin):
    __tablename__ = "trusted_contacts"

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
        unique=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    relationship = Column(String(100), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    consent_given = Column(Boolean, default=False, nullable=False)
    notification_level = Column(
        String(50), default="critical_only", nullable=False
    )  # Enum: high_and_critical | critical_only

    user = sa_relationship("User", back_populates="trusted_contact")


    __table_args__ = (
        Index("ix_trusted_contacts_user_enabled", "user_id", "enabled"),
    )
