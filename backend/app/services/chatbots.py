"""Business logic for chatbot operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from slugify import slugify
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chatbot, Document, DocumentStatus, User
from app.schemas import ChatbotCreate


class ChatbotService:
    """Encapsulates CRUD operations for chatbots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Chatbot]:
        statement = (
            select(Chatbot)
            .where(Chatbot.owner_id == user_id)
            .order_by(Chatbot.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_for_user(self, chatbot_id: UUID, user_id: UUID) -> Chatbot | None:
        statement = select(Chatbot).where(
            Chatbot.id == chatbot_id, Chatbot.owner_id == user_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, owner: User, payload: ChatbotCreate) -> Chatbot:
        slug = await self._generate_unique_slug(payload.name, owner.id)
        chatbot = Chatbot(
            owner_id=owner.id,
            name=payload.name,
            slug=slug,
            system_prompt=payload.system_prompt,
            model_provider=payload.model_provider,
            model_name=payload.model_name,
            temperature=payload.temperature,
            top_k=payload.top_k,
        )
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)
        return chatbot

    async def ensure_owner(self, chatbot_id: UUID, user_id: UUID) -> Chatbot:
        chatbot = await self.get_for_user(chatbot_id, user_id)
        if not chatbot:
            raise PermissionError("Chatbot not found or access denied")
        return chatbot

    async def _generate_unique_slug(self, name: str, owner_id: UUID) -> str:
        base_slug = slugify(name) or slugify(uuid4().hex[:8])
        slug_candidate = base_slug
        suffix = 1

        while await self._slug_exists(slug_candidate, owner_id):
            suffix += 1
            slug_candidate = f"{base_slug}-{suffix}"
        return slug_candidate

    async def _slug_exists(self, slug: str, owner_id: UUID) -> bool:
        stmt: Select[tuple[int]] = select(func.count()).select_from(Chatbot).where(
            Chatbot.slug == slug, Chatbot.owner_id == owner_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0


class DocumentService:
    """Manages uploaded documents for chatbots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_document(
        self,
        *,
        chatbot_id: UUID,
        uploader_id: UUID,
        file_name: str,
        storage_path: str,
        mime_type: str,
        size_bytes: int,
        checksum: str | None = None,
    ) -> Document:
        document = Document(
            chatbot_id=chatbot_id,
            uploaded_by=uploader_id,
            file_name=file_name,
            file_path=storage_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum=checksum,
            status=DocumentStatus.PENDING.value,
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_for_chatbot(
        self, document_id: UUID, chatbot_id: UUID, owner_id: UUID
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.chatbot_id == chatbot_id,
            Document.chatbot.has(Chatbot.owner_id == owner_id),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_chatbot(self, chatbot_id: UUID, owner_id: UUID) -> list[Document]:
        statement = (
            select(Document)
            .where(
                Document.chatbot_id == chatbot_id,
                Document.chatbot.has(Chatbot.owner_id == owner_id),
            )
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update_status(
        self,
        document: Document,
        status: DocumentStatus,
        *,
        error: str | None = None,
    ) -> Document:
        document.status = status.value if isinstance(status, DocumentStatus) else status
        document.error = error
        await self.session.commit()
        await self.session.refresh(document)
        return document