"""Conversation logging models."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from app.models.chatbot import Chatbot
    from app.models.user import User


class Conversation(TimestampMixin, Base):
    """Tracks a conversation session for a chatbot."""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    chatbot_id: Mapped[UUID] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    visitor_id: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(String(200))
    attributes: Mapped[dict | None] = mapped_column(JSON)

    chatbot: Mapped[Chatbot] = relationship(back_populates="conversations")
    user: Mapped[User | None] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    usage_logs: Mapped[list[UsageLog]] = relationship(back_populates="conversation")


class MessageRole(str, Enum):
    """Message sender roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(TimestampMixin, Base):
    """Individual messages exchanged in a conversation."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLAlchemyEnum(
            MessageRole,
            name="message_role",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    attributes: Mapped[dict | None] = mapped_column(JSON)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class UsageEvent(str, Enum):
    """Enumeration of tracked usage events."""

    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    ERROR = "error"


class UsageLog(TimestampMixin, Base):
    """Tracks usage metrics for analytics and rate limiting."""

    __tablename__ = "usage_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    chatbot_id: Mapped[UUID] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), index=True
    )
    event_type: Mapped[UsageEvent] = mapped_column(
        SQLAlchemyEnum(
            UsageEvent,
            name="usage_event",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status_code: Mapped[int | None] = mapped_column(Integer)
    attributes: Mapped[dict | None] = mapped_column(JSON)

    chatbot: Mapped[Chatbot] = relationship(back_populates="usage_logs")
    user: Mapped[User | None] = relationship(back_populates="usage_logs")
    conversation: Mapped[Conversation | None] = relationship(back_populates="usage_logs")

