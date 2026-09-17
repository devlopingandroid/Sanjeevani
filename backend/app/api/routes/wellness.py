"""API Router for Multimodal Wellness Context & YouTube Exercise Video Integration."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.wellness_context import MultimodalWellnessResponse
from app.schemas.youtube import ExerciseVideosResponse
from app.services.wellness_context_service import WellnessContextService
from app.services.youtube_service import YouTubeService, YouTubeServiceError

router = APIRouter(tags=["Multimodal Wellness Context & Exercises"])


@router.get(
    "/wellness-context",
    response_model=MultimodalWellnessResponse,
    summary="Get user's multimodal wellness context",
)
def get_multimodal_wellness_context(
    conversation_id: Optional[str] = Query(None, description="Optional conversation ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluates and returns the user's multimodal wellness context combining biosensor and chat signals."""
    return WellnessContextService.evaluate_context(
        db=db, user=current_user, conversation_id=conversation_id
    )


@router.get(
    "/wellness/exercises/{exercise_name}/videos",
    response_model=ExerciseVideosResponse,
    summary="Get instructional YouTube videos for exercise/yoga posture",
)
async def get_exercise_videos(
    exercise_name: str = Path(..., description="Exercise or yoga posture name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches real instructional YouTube videos for an exercise pose via YouTube Data API v3 with DB caching."""
    try:
        return await YouTubeService.get_exercise_videos(
            db=db, exercise_name=exercise_name
        )
    except YouTubeServiceError as err:
        raise HTTPException(status_code=err.status_code, detail=str(err))

