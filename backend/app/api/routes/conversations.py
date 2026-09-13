"""Conversations and Chat History API routes for SANJEEVNI."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    PaginatedConversationsResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    PaginatedMessagesResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["Conversations & Chat History"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Creates a new conversation container belonging strictly to the authenticated user.",
)
def create_conversation(
    payload: Optional[ConversationCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = payload.title if payload else None
    return ChatService.create_conversation(db=db, user_id=current_user.id, title=title)


@router.get(
    "",
    response_model=PaginatedConversationsResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's conversations",
    description="Retrieves a paginated list of conversations owned by the authenticated user ordered by updated_at DESC.",
)
def list_conversations(
    status_filter: Optional[str] = Query("active", alias="status", description="Filter by status ('active' or 'archived')"),
    limit: int = Query(20, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = ChatService.list_conversations(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return PaginatedConversationsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation details",
    description="Fetches details for a specific conversation. Enforces ownership strictly; returns 404 if not owned.",
)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ChatService.get_conversation(db=db, conversation_id=conversation_id, user_id=current_user.id)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation",
    description="Deletes a conversation and its messages. Enforces ownership strictly; returns 404 if not owned.",
)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ChatService.delete_conversation(db=db, conversation_id=conversation_id, user_id=current_user.id)
    return {"status": "success", "message": "Conversation deleted successfully"}


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a message in conversation",
    description="Appends a new immutable message to an existing conversation owned by the authenticated user.",
)
def create_message(
    conversation_id: str,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ChatService.add_message(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        role=payload.role,
        message_text=payload.message,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=PaginatedMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="List messages in conversation",
    description="Retrieves a paginated list of messages for a conversation ordered chronologically (created_at ASC).",
)
def list_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = ChatService.get_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return PaginatedMessagesResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
