"""YouTube Data API v3 Backend Service with Database Caching.

Fetches real instructional exercise/yoga video metadata via the official
YouTube Data API v3 while enforcing the strict ZERO-MOCK policy:
- Key remains backend-only in settings/environment.
- Results are cached in the PostgreSQL/SQLite `youtube_video_cache` table for 24 hours.
- Returns clean, uninvented data or an honest empty list if API key is unconfigured or quota is exceeded.
"""
import html
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.youtube_video_cache import YouTubeVideoCache
from app.schemas.youtube import YouTubeVideoItem, ExerciseVideosResponse


class YouTubeServiceError(Exception):
    """Custom exception for YouTube service errors with HTTP status and category."""

    def __init__(self, message: str, status_code: int = 502, category: str = "API_ERROR"):
        super().__init__(message)
        self.status_code = status_code
        self.category = category


class YouTubeService:
    CACHE_DURATION_HOURS = 24

    @classmethod
    def _construct_search_query(cls, exercise_name: str) -> str:
        """Constructs a safe, targeted search query for exercise/yoga instructional videos."""
        clean_name = exercise_name.strip()
        # Avoid double terms if already contains yoga/exercise
        lower_name = clean_name.lower()
        if "yoga" in lower_name or "pose" in lower_name or "asana" in lower_name:
            return f"{clean_name} posture tutorial"
        return f"{clean_name} yoga exercise proper form"

    @classmethod
    async def get_exercise_videos(
        cls,
        db: Session,
        exercise_name: str,
        max_results: Optional[int] = None,
    ) -> ExerciseVideosResponse:
        """Gets instructional YouTube videos for a given exercise with DB caching.

        Args:
            db: SQLAlchemy Database Session.
            exercise_name: Target exercise or yoga pose name.
            max_results: Max results limit (default from config).

        Returns:
            ExerciseVideosResponse
        Raises:
            YouTubeServiceError on configuration, API, or network failure.
        """
        clean_exercise = exercise_name.strip()
        limit = max_results or settings.YOUTUBE_MAX_RESULTS
        now = datetime.now(timezone.utc)

        # 1. Check Database Cache
        cached_records = (
            db.query(YouTubeVideoCache)
            .filter(
                YouTubeVideoCache.exercise_name == clean_exercise,
                YouTubeVideoCache.expires_at > now,
            )
            .all()
        )

        if cached_records:
            logger.info(f"YouTubeCache hit for exercise '{clean_exercise}' ({len(cached_records)} cached videos).")
            videos = [
                YouTubeVideoItem(
                    video_id=rec.video_id,
                    title=rec.title,
                    description=rec.description or "",
                    thumbnail_url=rec.thumbnail_url,
                    channel_title=rec.channel_title,
                    published_at=rec.published_at,
                    youtube_url=rec.youtube_url,
                )
                for rec in cached_records[:limit]
            ]
            return ExerciseVideosResponse(exercise=clean_exercise, videos=videos)

        # 2. Cache Miss: Check API Key Configuration
        api_key = settings.YOUTUBE_API_KEY
        if not api_key or not api_key.strip():
            logger.warning(f"YOUTUBE_API_KEY not configured on backend for exercise '{clean_exercise}'.")
            raise YouTubeServiceError(
                "Video service is temporarily unavailable.",
                status_code=503,
                category="CONFIG_ERROR",
            )

        # 3. Call Official YouTube Data API v3 Search Endpoint
        query = cls._construct_search_query(clean_exercise)
        base_url = settings.YOUTUBE_API_BASE_URL.rstrip('/')
        search_endpoint = f"{base_url}/search" if not base_url.endswith("/search") else base_url

        params = {
            "key": api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "videoEmbeddable": "true",
            "maxResults": limit,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_endpoint, params=params)

            if response.status_code != 200:
                logger.error(f"YouTube API returned HTTP {response.status_code}: {response.text}")
                if response.status_code in (401, 403):
                    raise YouTubeServiceError(
                        "Video service is temporarily unavailable.",
                        status_code=503,
                        category="CONFIG_ERROR",
                    )
                elif response.status_code == 429:
                    raise YouTubeServiceError(
                        "Videos are temporarily unavailable.",
                        status_code=429,
                        category="RATE_LIMIT",
                    )
                else:
                    raise YouTubeServiceError(
                        "Videos are temporarily unavailable.",
                        status_code=502,
                        category="API_ERROR",
                    )

            data = response.json()
            items = data.get("items", [])

            videos: List[YouTubeVideoItem] = []
            expires_at = now + timedelta(hours=cls.CACHE_DURATION_HOURS)

            # Clear old expired records for this exercise before inserting new cache entries
            db.query(YouTubeVideoCache).filter(
                YouTubeVideoCache.exercise_name == clean_exercise
            ).delete()

            for item in items:
                snippet = item.get("snippet", {})
                id_obj = item.get("id", {})
                video_id = id_obj.get("videoId")

                if not video_id:
                    continue

                raw_title = snippet.get("title", "")
                clean_title = html.unescape(raw_title)
                clean_desc = html.unescape(snippet.get("description", ""))
                clean_channel = html.unescape(snippet.get("channelTitle", ""))
                pub_at = snippet.get("publishedAt")

                thumbnails = snippet.get("thumbnails", {})
                thumb_url = (
                    thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url")
                    or thumbnails.get("default", {}).get("url")
                    or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                )

                yt_url = f"https://www.youtube.com/watch?v={video_id}"

                video_item = YouTubeVideoItem(
                    video_id=video_id,
                    title=clean_title,
                    description=clean_desc,
                    thumbnail_url=thumb_url,
                    channel_title=clean_channel,
                    published_at=pub_at,
                    youtube_url=yt_url,
                )
                videos.append(video_item)

                # Persist in DB Cache
                cache_rec = YouTubeVideoCache(
                    id=str(uuid.uuid4()),
                    exercise_name=clean_exercise,
                    video_id=video_id,
                    title=clean_title,
                    description=clean_desc,
                    thumbnail_url=thumb_url,
                    channel_title=clean_channel,
                    published_at=pub_at,
                    youtube_url=yt_url,
                    fetched_at=now,
                    expires_at=expires_at,
                )
                db.add(cache_rec)

            db.commit()
            logger.info(f"Successfully fetched and cached {len(videos)} YouTube videos for '{clean_exercise}'.")
            return ExerciseVideosResponse(exercise=clean_exercise, videos=videos)

        except YouTubeServiceError:
            db.rollback()
            raise
        except (httpx.TimeoutException, TimeoutError) as exc:
            logger.error(f"Timeout fetching YouTube videos for exercise '{clean_exercise}': {exc}")
            db.rollback()
            raise YouTubeServiceError(
                "Unable to load videos. Please try again.",
                status_code=504,
                category="NETWORK_ERROR",
            )
        except Exception as exc:
            logger.error(f"Unexpected error fetching YouTube videos for exercise '{clean_exercise}': {exc}")
            db.rollback()
            raise YouTubeServiceError(
                "Videos are temporarily unavailable.",
                status_code=502,
                category="API_ERROR",
            )
