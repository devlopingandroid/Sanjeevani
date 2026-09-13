"""Pydantic schemas for YouTube Video Search results."""
from typing import List, Optional
from pydantic import BaseModel, Field


class YouTubeVideoItem(BaseModel):
    video_id: str = Field(..., description="Official YouTube Video ID")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(default="", description="Video snippet description")
    thumbnail_url: str = Field(..., description="URL of high-resolution video thumbnail")
    channel_title: str = Field(..., description="YouTube channel name")
    published_at: Optional[str] = Field(default=None, description="ISO timestamp of publishing date")
    youtube_url: str = Field(..., description="Official YouTube watch URL (https://www.youtube.com/watch?v=...)")


class ExerciseVideosResponse(BaseModel):
    exercise: str = Field(..., description="Exercise or posture name")
    videos: List[YouTubeVideoItem] = Field(default_factory=list, description="List of matching YouTube instructional videos")
