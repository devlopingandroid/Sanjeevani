"""API Endpoints for Emotion and Distress Analysis (Phase 3)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.emotion import EmotionalAssessmentResponse
from app.services.emotion_service import EmotionAnalysisService

router = APIRouter(prefix="/conversations", tags=["Emotion & Distress Analysis"])


@router.get(
    "/{conversation_id}/messages/{message_id}/assessment",
    response_model=EmotionalAssessmentResponse,
    summary="Get emotional assessment for a chat message",
)
def get_message_assessment(
    conversation_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves emotional assessment for a message with strict ownership verification."""
    assessment = EmotionAnalysisService.get_assessment_by_message(
        db=db, message_id=message_id, user_id=current_user.id
    )
    if not assessment or assessment.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emotional assessment not found or access denied.",
        )
    return assessment


@router.get(
    "/{conversation_id}/assessments",
    response_model=List[EmotionalAssessmentResponse],
    summary="List all emotional assessments in a conversation",
)
def list_conversation_assessments(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all emotional assessments in a conversation with strict ownership verification."""
    assessments = EmotionAnalysisService.list_assessments_for_conversation(
        db=db, conversation_id=conversation_id, user_id=current_user.id
    )
    if not assessments:
        from app.services.chat_service import ChatService
        try:
            ChatService.get_conversation(db, conversation_id, current_user.id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )
    return assessments
