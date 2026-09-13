"""AI Chat routing endpoints for SANJEEVNI.

Proxies requests to the Mistral AI service while validating authentication tokens
and isolating health telemetry strictly to the requesting user.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI & Wellness Companion"])


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Sanjeevni AI (Mistral)",
    description="Securely evaluates wellness questions using Mistral AI, attaching verified physiological telemetry if available.",
)
async def chat_with_ai(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AIService.chat(
        db=db,
        user=current_user,
        message=request.message,
        conversation_history=request.conversation_history,
        conversation_id=request.conversation_id,
        include_health_context=request.include_health_context,
    )
