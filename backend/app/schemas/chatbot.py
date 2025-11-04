"""Schemas for chatbot configuration and documents."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.chatbot import DocumentStatus


class ChatbotBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model_provider: str = Field(min_length=1, max_length=50)
    model_name: str = Field(min_length=1, max_length=50)
    system_prompt: str = Field(default="", max_length=5000)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    top_k: int = Field(default=4, ge=1, le=20)


class ChatbotCreate(ChatbotBase):
    pass


class ChatbotRead(ChatbotBase):
    id: UUID
    slug: str
    deployment_slug: str | None = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: UUID
    file_name: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


