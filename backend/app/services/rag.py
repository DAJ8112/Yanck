"""High-level Retrieval-Augmented Generation orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Iterable, Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Chatbot, Chunk, Document
from app.services.embeddings import EmbeddingService
from app.services.providers import GeminiClient, GeminiProviderError
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_BEHAVIOR_PROMPT = (
    "You are a helpful assistant that answers questions using the provided context from the "
    "user's knowledge base. If the context does not contain the answer, politely explain that "
    "the information is unavailable."
)


@dataclass(slots=True)
class RetrievedChunk:
    """Represents a chunk retrieved from the vector store."""

    id: UUID
    document_id: UUID
    document_name: str | None
    score: float
    content: str


@dataclass(slots=True)
class RAGResponse:
    """Final response from the RAG pipeline."""

    answer: str
    chunks: list[RetrievedChunk]


class RAGGenerationError(RuntimeError):
    """Raised when the RAG pipeline cannot complete successfully."""


def _parse_safety_settings(raw: str | None) -> list[dict[str, str]] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:  # pragma: no cover - configuration-time issue
        logger.warning("Unable to parse GEMINI_SAFETY_SETTINGS; continuing without overrides")
        return None
    if not isinstance(parsed, Iterable):
        logger.warning(
            "GEMINI_SAFETY_SETTINGS must be a JSON array of safety configuration objects"
        )
        return None

    result: list[dict[str, str]] = []
    for item in parsed:
        if isinstance(item, dict):
            result.append({str(key): str(value) for key, value in item.items()})
    return result or None


class RAGService:
    """Coordinate retrieval and generation for chatbot conversations."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        client: GeminiClient | None = None,
        embedder: EmbeddingService | None = None,
    ) -> None:
        self.session = session
        self.embedder = embedder or EmbeddingService()
        self.top_k = max(settings.rag_top_k, 1)
        self._client: GeminiClient | None = client

    async def generate_response(
        self,
        chatbot: Chatbot,
        user_message: str,
        *,
        history: Sequence[tuple[str, str]] | None = None,
        top_k: int | None = None,
    ) -> RAGResponse:
        """Produce an answer grounded in the chatbot's knowledge base."""

        if not user_message.strip():
            raise ValueError("User message must not be empty")

        query_vector = self.embedder.embed_query(user_message)
        if not query_vector:
            raise RAGGenerationError("Failed to generate embedding for the user query")

        vector_store = VectorStore(settings.vector_store_path, chatbot.id, len(query_vector))
        search_results = vector_store.similarity_search(query_vector, top_k or self.top_k)

        retrieved_chunks = await self._load_chunks(chatbot.id, search_results)

        context_text = self._build_context(retrieved_chunks)

        system_prompt = "\n\n".join(
            filter(None, [DEFAULT_BEHAVIOR_PROMPT, chatbot.system_prompt])
        ).strip()

        conversation_messages = list(self._normalise_history(history))
        conversation_messages.append(
            (
                "user",
                self._compose_user_prompt(user_message, context_text),
            )
        )

        generation_config = {
            "temperature": chatbot.temperature,
            "max_output_tokens": 1024,
        }

        client = self._get_client()

        try:
            answer = await client.generate(
                system_prompt=system_prompt,
                messages=conversation_messages,
                generation_config=generation_config,
            )
        except GeminiProviderError as exc:
            raise RAGGenerationError(str(exc)) from exc

        return RAGResponse(answer=answer, chunks=retrieved_chunks)

    async def _load_chunks(
        self,
        chatbot_id: UUID,
        search_results: list[tuple[str, float]],
    ) -> list[RetrievedChunk]:
        if not search_results:
            return []

        ordered_ids: list[UUID] = []
        score_map: dict[UUID, float] = {}

        for chunk_id_str, score in search_results:
            try:
                chunk_id = UUID(chunk_id_str)
            except ValueError:
                logger.warning("Skipping malformed chunk id from vector store: %s", chunk_id_str)
                continue
            if chunk_id in score_map:
                continue
            ordered_ids.append(chunk_id)
            score_map[chunk_id] = score

        if not ordered_ids:
            return []

        stmt: Select[tuple[Chunk, Document]] = (
            select(Chunk, Document)
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.chatbot_id == chatbot_id, Chunk.id.in_(ordered_ids))
        )
        result = await self.session.execute(stmt)

        chunk_map: dict[UUID, RetrievedChunk] = {}
        for chunk, document in result.all():
            chunk_map[chunk.id] = RetrievedChunk(
                id=chunk.id,
                document_id=chunk.document_id,
                document_name=document.file_name,
                score=score_map.get(chunk.id, 0.0),
                content=chunk.content,
            )

        return [chunk_map[chunk_id] for chunk_id in ordered_ids if chunk_id in chunk_map]

    def _get_client(self) -> GeminiClient:
        if self._client is not None:
            return self._client

        try:
            self._client = GeminiClient(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                safety_settings=_parse_safety_settings(settings.gemini_safety_settings),
            )
        except (ValueError, ImportError) as exc:
            raise RAGGenerationError(str(exc)) from exc

        return self._client

    @staticmethod
    def _normalise_history(
        history: Sequence[tuple[str, str]] | None,
    ) -> Iterable[tuple[str, str]]:
        if not history:
            return []

        normalised: list[tuple[str, str]] = []
        for role, content in history:
            if role.lower() in {"assistant", "model"}:
                normalised.append(("model", content))
            elif role.lower() == "user":
                normalised.append(("user", content))
            else:
                logger.debug("Skipping unsupported conversation role: %s", role)
        return normalised

    @staticmethod
    def _build_context(chunks: Sequence[RetrievedChunk]) -> str:
        if not chunks:
            return ""

        blocks = []
        for index, chunk in enumerate(chunks, start=1):
            header = f"[{index}] Source: {chunk.document_name or chunk.document_id} (score: {chunk.score:.3f})"
            blocks.append(f"{header}\n{chunk.content.strip()}")
        return "\n\n".join(blocks)

    @staticmethod
    def _compose_user_prompt(message: str, context: str) -> str:
        context_block = context or "No relevant context was retrieved from the knowledge base."
        instructions = (
            "Use the provided context snippets to answer the user's latest question. "
            "If the context is empty or insufficient, clearly state that the answer is not available."
        )
        return (
            f"{instructions}\n\nContext:\n{context_block}\n\n"
            f"User question:\n{message.strip()}"
        )

