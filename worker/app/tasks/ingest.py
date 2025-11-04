from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Sequence
from uuid import UUID

from worker.main import celery_app
from app.core.config import settings

from backend.app.db.session import SessionLocal
from backend.app.models import Chunk, Document, DocumentStatus, Embedding
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.storage import S3StorageService
from backend.app.services.text import chunk_text, extract_text_from_file
from backend.app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


@celery_app.task(name="worker.tasks.ingest_document")
def ingest_document_task(document_id: str) -> None:
    asyncio.run(_ingest_document(UUID(document_id)))


async def _ingest_document(document_id: UUID) -> None:
    async with SessionLocal() as session:  # type: ignore[call-arg]
        document = await session.get(Document, document_id)
        if not document:
            logger.warning("Document %s not found", document_id)
            return

        await _update_status(session, document, DocumentStatus.PROCESSING)

        storage = S3StorageService(
            bucket_name=settings.s3_bucket_name,
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = Path(tmpdir) / Path(document.file_name).name
            await storage.download_file(document.file_path, local_path)

            try:
                raw_text = extract_text_from_file(local_path, document.mime_type)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to extract text for %s", document_id)
                await _update_status(session, document, DocumentStatus.FAILED, str(exc))
                return

        chunks = chunk_text(raw_text)
        if not chunks:
            await _update_status(
                session,
                document,
                DocumentStatus.FAILED,
                "No textual content detected in document.",
            )
            return

        embedding_service = EmbeddingService()
        vectors = embedding_service.embed_documents(chunks)
        dimension = len(vectors[0])

        chunk_ids = await _persist_chunks(session, document, chunks, vectors)

        vector_store = VectorStore(settings.vector_store_path, document.chatbot_id, dimension)
        vector_store.add_embeddings(vectors, chunk_ids)

        await _update_status(session, document, DocumentStatus.READY)


async def _persist_chunks(
    session, document: Document, chunks: Sequence[str], vectors: Sequence[Sequence[float]]
) -> list[str]:
    created_ids: list[str] = []
    for index, (text, embedding_vec) in enumerate(zip(chunks, vectors)):
        chunk = Chunk(
            chatbot_id=document.chatbot_id,
            document_id=document.id,
            chunk_index=index,
            content=text,
            token_count=len(text.split()),
        )
        session.add(chunk)
        await session.flush()
        created_ids.append(str(chunk.id))

        embedding = Embedding(
            chunk_id=chunk.id,
            dimension=len(embedding_vec),
            embedding_model="local-mini-encoder",
            vector=list(embedding_vec),
        )
        session.add(embedding)

    await session.commit()
    await session.refresh(document)
    return created_ids


async def _update_status(
    session, document: Document, status: DocumentStatus, error: str | None = None
) -> None:
    document.status = status
    document.error = error
    await session.commit()
    await session.refresh(document)
