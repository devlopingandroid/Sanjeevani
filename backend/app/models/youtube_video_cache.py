"""YouTubeVideoCache database model for caching exercise video metadata."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Index

from app.db.database import Base


class YouTubeVideoCache(Base):
    __tablename__ = "youtube_video_cache"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    exercise_name = Column(String(100), nullable=False, index=True)
    video_id = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=False)
    channel_title = Column(String(255), nullable=False)
    published_at = Column(String(50), nullable=True)
    youtube_url = Column(String(500), nullable=False)
    fetched_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_youtube_video_cache_exercise_expires", "exercise_name", "expires_at"),
    )
