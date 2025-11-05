"""Schemas supporting chatbot conversations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import MessageRole


class ChatRequest(BaseModel):
    """Payload for initiating or continuing a chatbot conversation."""

    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatContextChunk(BaseModel):
    """Metadata about a retrieved knowledge chunk used for grounding the answer."""

    id: UUID
    document_id: UUID
    document_name: str | None = None
    score: float
    content: str


class ChatMessage(BaseModel):
    """Read-model for persisted conversation messages."""

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Response containing the assistant reply and supporting context."""

    conversation_id: UUID
    reply: ChatMessage
    context: list[ChatContextChunk]
    created_new_conversation: bool = False


