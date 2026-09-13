"""API Endpoints for Phase 4 Deterministic Distress Risk Engine."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.risk import RiskEventResponse
from app.services.risk_engine import RiskEngineService

router = APIRouter(prefix="/conversations", tags=["Risk Engine & Escalation"])


@router.get(
    "/{conversation_id}/risk-events",
    response_model=List[RiskEventResponse],
    summary="List all authoritative risk events in a conversation",
)
def list_conversation_risk_events(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all authoritative risk events in a conversation with strict user ownership verification."""
    events = RiskEngineService.get_risk_events_for_conversation(
        db=db, conversation_id=conversation_id, user_id=current_user.id
    )
    if not events:
        from app.services.chat_service import ChatService
        try:
            ChatService.get_conversation(db, conversation_id, current_user.id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )
    return events
