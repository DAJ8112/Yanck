"""Celery application instance for asynchronous workloads."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "rag_backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="default",
)


def enqueue_document_ingestion(document_id: str) -> None:
    """Dispatch a Celery task to ingest an uploaded document."""

    celery_app.send_task("worker.tasks.ingest_document", args=[document_id])



