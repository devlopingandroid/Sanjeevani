"""Service layer for managing Sanjeevni AI Conversations and Chat Messages."""
from typing import List, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ChatMessage
from app.core.exceptions import SanjeevniException, ErrorCode


class ChatService:
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: int,
        title: Optional[str] = None,
    ) -> Conversation:
        """Creates a new conversation belonging strictly to the authenticated user."""
        clean_title = title.strip() if title and title.strip() else None
        conversation = Conversation(
            user_id=user_id,
            title=clean_title,
            status="active",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def list_conversations(
        db: Session,
        user_id: int,
        status: Optional[str] = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Conversation], int]:
        """Lists conversations owned by user_id ordered by updated_at DESC."""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if status:
            query = query.filter(Conversation.status == status)

        total = query.count()
        items = (
            query.order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: str,
        user_id: int,
    ) -> Conversation:
        """Retrieves conversation by id. Enforces server-side ownership check."""
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation or conversation.user_id != user_id:
            raise SanjeevniException(
                status_code=404,
                error_code=ErrorCode.NOT_FOUND,
                message="Conversation not found or access denied.",
            )
        return conversation

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: str,
        user_id: int,
    ) -> None:
        """Deletes a conversation and its messages. Enforces ownership check."""
        conversation = ChatService.get_conversation(db, conversation_id, user_id)
        db.delete(conversation)
        db.commit()

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        user_id: int,
        role: str,
        message_text: str,
    ) -> ChatMessage:
        """Appends a new immutable message to conversation. Enforces ownership."""
        conversation = ChatService.get_conversation(db, conversation_id, user_id)

        clean_message = message_text.strip()
        chat_msg = ChatMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role=role,
            message=clean_message,
        )
        db.add(chat_msg)

        # Update conversation timestamp & auto-set title if blank
        conversation.updated_at = datetime.now(timezone.utc)
        if not conversation.title and role == "user":
            conversation.title = clean_message[:50]

        db.commit()
        db.refresh(chat_msg)
        return chat_msg

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ChatMessage], int]:
        """Lists messages for a conversation ordered chronologically by created_at ASC."""
        conversation = ChatService.get_conversation(db, conversation_id, user_id)

        query = db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation.id)
        total = query.count()
        items = (
            query.order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total
