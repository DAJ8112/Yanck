"""Chatbot domain models."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
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

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from app.models.conversation import Conversation, UsageLog
    from app.models.user import User


class Chatbot(TimestampMixin, Base):
    """Stores chatbot configuration and deployment metadata."""

    __tablename__ = "chatbots"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    temperature: Mapped[float] = mapped_column(default=0.2, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    deployment_slug: Mapped[str | None] = mapped_column(String(160), unique=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    owner: Mapped[User] = relationship(back_populates="chatbots")
    documents: Mapped[list[Document]] = relationship(
        back_populates="chatbot", cascade="all, delete-orphan"
    )
    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="chatbot", cascade="all, delete-orphan"
    )
    conversations: Mapped[list[Conversation]] = relationship(back_populates="chatbot")
    usage_logs: Mapped[list[UsageLog]] = relationship(back_populates="chatbot")


class DocumentStatus(str, Enum):
    """Lifecycle status values for uploaded documents."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(TimestampMixin, Base):
    """Uploaded source document metadata."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    chatbot_id: Mapped[UUID] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), index=True, nullable=False
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[DocumentStatus] = mapped_column(
        SQLAlchemyEnum(
            DocumentStatus,
            name="document_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=DocumentStatus.PENDING.value,
    )
    error: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict | None] = mapped_column(JSON)

    chatbot: Mapped[Chatbot] = relationship(back_populates="documents")
    uploader: Mapped[User] = relationship(back_populates="documents")
    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(TimestampMixin, Base):
    """Individual knowledge chunks derived from documents."""

    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    chatbot_id: Mapped[UUID] = mapped_column(
        ForeignKey("chatbots.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)

    chatbot: Mapped[Chatbot] = relationship(back_populates="chunks")
    document: Mapped[Document] = relationship(back_populates="chunks")
    embedding: Mapped[Embedding | None] = relationship(
        back_populates="chunk", cascade="all, delete-orphan", uselist=False
    )


class Embedding(TimestampMixin, Base):
    """Vector embeddings associated with chunks."""

    __tablename__ = "embeddings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    chunk_id: Mapped[UUID] = mapped_column(
        ForeignKey("chunks.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    vector: Mapped[list[float]] = mapped_column(JSON, nullable=False)

    chunk: Mapped[Chunk] = relationship(back_populates="embedding")

