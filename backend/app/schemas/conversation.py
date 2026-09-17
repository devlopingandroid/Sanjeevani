"""Pydantic schemas for Conversation and ChatMessage objects."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ChatMessageCreate(BaseModel):
    role: str = Field(..., description="Role of the message sender: 'user' or 'assistant'")
    message: str = Field(..., min_length=1, description="Message text content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_clean = v.lower().strip()
        if v_clean not in ("user", "assistant"):
            raise ValueError("Role must be either 'user' or 'assistant'.")
        return v_clean

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or blank.")
        return v.strip()


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    user_id: int
    role: str
    message: str
    created_at: datetime


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255, description="Optional conversation title")


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    title: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime



class PaginatedConversationsResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
    limit: int
    offset: int


class PaginatedMessagesResponse(BaseModel):
    items: List[ChatMessageResponse]
    total: int
    limit: int
    offset: int
