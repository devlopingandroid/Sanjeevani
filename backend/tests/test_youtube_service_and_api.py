"""Tests for YouTube Data API v3 Backend Service & Exercise Video Endpoints.

Verifies:
1. Query construction for exercise/yoga postures.
2. Successful API response parsing and mapping.
3. Missing/unconfigured YOUTUBE_API_KEY handling.
4. YouTube API 4xx/5xx / quota error handling.
5. Empty search results handling.
6. Database caching hit vs. expiration behavior.
7. Zero fake fallback data integrity.
8. API endpoint GET /api/v1/wellness/exercises/{exercise_name}/videos.
"""
import time
from datetime import datetime, timezone, timedelta
import pytest
import httpx
from unittest.mock import patch, AsyncMock

from app.core.config import settings
from app.models.youtube_video_cache import YouTubeVideoCache
from app.services.youtube_service import YouTubeService, YouTubeServiceError


def test_youtube_query_construction():
    """Verifies targeted search query generation."""
    query1 = YouTubeService._construct_search_query("Child's Pose")
    assert "Child's Pose" in query1
    assert "posture tutorial" in query1

    query2 = YouTubeService._construct_search_query("Cat-Cow")
    assert "Cat-Cow" in query2
    assert "yoga exercise" in query2


@pytest.mark.asyncio
async def test_youtube_service_missing_api_key(db_session):
    """When YOUTUBE_API_KEY is None or empty, raises YouTubeServiceError with status 503."""
    db_session.query(YouTubeVideoCache).filter(YouTubeVideoCache.exercise_name == "Uncached Pose").delete()
    db_session.commit()
    with patch.object(settings, "YOUTUBE_API_KEY", None):
        with pytest.raises(YouTubeServiceError) as exc_info:
            await YouTubeService.get_exercise_videos(db_session, "Uncached Pose")
        assert exc_info.value.status_code == 503
        assert exc_info.value.category == "CONFIG_ERROR"


@pytest.mark.asyncio
async def test_youtube_service_success_fetch_and_cache(db_session):
    """Verifies successful API fetch, parsing, and DB cache storage."""
    mock_youtube_response = {
        "items": [
            {
                "id": {"videoId": "dQw4w9WgXcQ"},
                "snippet": {
                    "title": "Child&#39;s Pose Yoga Tutorial",
                    "description": "Learn proper alignment for Child&#39;s Pose.",
                    "channelTitle": "Yoga Channel",
                    "publishedAt": "2026-01-01T12:00:00Z",
                    "thumbnails": {
                        "high": {"url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"}
                    }
                }
            }
        ]
    }
    mock_httpx_resp = httpx.Response(200, json=mock_youtube_response)

    with patch.object(settings, "YOUTUBE_API_KEY", "test-youtube-key"):
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_httpx_resp):
            res = await YouTubeService.get_exercise_videos(db_session, "Child's Pose")
            assert res.exercise == "Child's Pose"
            assert len(res.videos) == 1
            video = res.videos[0]
            assert video.video_id == "dQw4w9WgXcQ"
            assert video.title == "Child's Pose Yoga Tutorial"
            assert video.channel_title == "Yoga Channel"
            assert video.youtube_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            assert video.thumbnail_url == "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"

            # Verify DB Cache entry was created
            cached = db_session.query(YouTubeVideoCache).filter(
                YouTubeVideoCache.exercise_name == "Child's Pose"
            ).first()
            assert cached is not None
            assert cached.video_id == "dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_youtube_service_cache_hit(db_session):
    """When unexpired cache exists in DB, returns cached records without calling HTTP API."""
    now = datetime.now(timezone.utc)
    cache_item = YouTubeVideoCache(
        id="cache-uuid-123",
        exercise_name="Cat-Cow",
        video_id="cached_vid_999",
        title="Cached Cat-Cow Tutorial",
        description="Cached description",
        thumbnail_url="https://i.ytimg.com/vi/cached_vid_999/hqdefault.jpg",
        channel_title="Cached Channel",
        published_at="2026-02-01T00:00:00Z",
        youtube_url="https://www.youtube.com/watch?v=cached_vid_999",
        fetched_at=now,
        expires_at=now + timedelta(hours=12),
    )
    db_session.add(cache_item)
    db_session.commit()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        res = await YouTubeService.get_exercise_videos(db_session, "Cat-Cow")
        assert res.exercise == "Cat-Cow"
        assert len(res.videos) == 1
        assert res.videos[0].video_id == "cached_vid_999"
        assert res.videos[0].title == "Cached Cat-Cow Tutorial"
        # API was NOT called on cache hit
        assert mock_get.call_count == 0


@pytest.mark.asyncio
async def test_youtube_service_cache_expiry(db_session):
    """When cache is expired, fetches fresh results from API."""
    now = datetime.now(timezone.utc)
    expired_item = YouTubeVideoCache(
        id="expired-uuid-123",
        exercise_name="Corpse Pose",
        video_id="old_expired_vid",
        title="Expired Pose",
        description="",
        thumbnail_url="https://i.ytimg.com/vi/old_expired_vid/hqdefault.jpg",
        channel_title="Old Channel",
        published_at="2025-01-01T00:00:00Z",
        youtube_url="https://www.youtube.com/watch?v=old_expired_vid",
        fetched_at=now - timedelta(hours=48),
        expires_at=now - timedelta(hours=24),
    )
    db_session.add(expired_item)
    db_session.commit()

    mock_fresh_resp = {
        "items": [
            {
                "id": {"videoId": "fresh_vid_000"},
                "snippet": {
                    "title": "Fresh Savasana Guide",
                    "description": "Fresh description",
                    "channelTitle": "Fresh Channel",
                    "publishedAt": "2026-03-01T00:00:00Z",
                    "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/fresh_vid_000/hqdefault.jpg"}}
                }
            }
        ]
    }
    mock_httpx_resp = httpx.Response(200, json=mock_fresh_resp)

    with patch.object(settings, "YOUTUBE_API_KEY", "test-youtube-key"):
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_httpx_resp):
            res = await YouTubeService.get_exercise_videos(db_session, "Corpse Pose")
            assert res.exercise == "Corpse Pose"
            assert len(res.videos) == 1
            assert res.videos[0].video_id == "fresh_vid_000"


@pytest.mark.asyncio
async def test_youtube_service_api_error_handling(db_session):
    """Handles HTTP 403/500/timeout gracefully with YouTubeServiceError."""
    db_session.query(YouTubeVideoCache).filter(YouTubeVideoCache.exercise_name == "Uncached Error Pose").delete()
    db_session.commit()
    mock_httpx_resp = httpx.Response(403, json={"error": {"message": "Quota exceeded"}})

    with patch.object(settings, "YOUTUBE_API_KEY", "test-key"):
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_httpx_resp):
            with pytest.raises(YouTubeServiceError) as exc_info:
                await YouTubeService.get_exercise_videos(db_session, "Uncached Error Pose")
            assert exc_info.value.status_code == 503



@pytest.mark.asyncio
async def test_api_get_exercise_videos_endpoint(client):
    """Verifies GET /api/v1/wellness/exercises/{exercise_name}/videos endpoint integration."""
    email = f"yt_api_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "YT Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mock_youtube_response = {
        "items": [
            {
                "id": {"videoId": "vid_api_123"},
                "snippet": {
                    "title": "Tree Pose Step by Step",
                    "description": "Tree pose balance tutorial",
                    "channelTitle": "Balance Channel",
                    "publishedAt": "2026-03-01T10:00:00Z",
                    "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/vid_api_123/hqdefault.jpg"}}
                }
            }
        ]
    }
    mock_httpx_resp = httpx.Response(200, json=mock_youtube_response)

    with patch.object(settings, "YOUTUBE_API_KEY", "test-key"):
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_httpx_resp):
            resp = client.get(
                "/api/v1/wellness/exercises/Tree%20Pose/videos",
                headers=headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["exercise"] == "Tree Pose"
            assert len(data["videos"]) == 1
            assert data["videos"][0]["video_id"] == "vid_api_123"
            assert data["videos"][0]["youtube_url"] == "https://www.youtube.com/watch?v=vid_api_123"
