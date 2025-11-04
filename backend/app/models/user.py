"""User domain models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from app.models.chatbot import Chatbot, Document
    from app.models.conversation import Conversation, UsageLog


class User(TimestampMixin, Base):
    """Represents a platform user."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_model_provider: Mapped[str] = mapped_column(
        String(50), default=settings.default_model_provider, nullable=False
    )
    default_model_name: Mapped[str] = mapped_column(
        String(50), default=settings.default_model_name, nullable=False
    )

    api_keys: Mapped[list[APIKey]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chatbots: Mapped[list[Chatbot]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship(back_populates="uploader")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="user")
    usage_logs: Mapped[list[UsageLog]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id!s}, email={self.email!r})"


class APIKey(TimestampMixin, Base):
    """Stores API credentials for third-party model providers."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False)
    last_four: Mapped[str] = mapped_column(String(4), nullable=False)

    user: Mapped[User] = relationship(back_populates="api_keys")

    def __repr__(self) -> str:
        return f"APIKey(id={self.id!s}, provider={self.provider!r})"

