"""xAI (Grok) request and response schemas."""
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., min_length=1)
    timestamp: Optional[str] = None


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User query to Sanjeevni AI")
    conversation_history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation identifier")
    include_health_context: bool = Field(default=True, description="Attach verified real biometric context if available")


class AIChatResponse(BaseModel):
    reply: str
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    model: str
    timestamp: str
    health_context_included: bool
    status: str = "success"
    scope: str = Field(default="HEALTH_WELLNESS", description="Domain scope indicator")
    handled_by: str = Field(default="MISTRAL_AI", description="'MISTRAL_AI' or 'DOMAIN_GUARD'")

