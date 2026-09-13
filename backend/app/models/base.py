"""Base model and mixins for SQLAlchemy models."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer
from app.db.database import Base


class TimestampMixin:
    """Provides created_at and updated_at timestamps in UTC."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
