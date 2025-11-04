# Worker Service

Celery-based worker responsible for document ingestion, chunking, embeddings, and vector index maintenance.

## Setup

```bash
uv sync
uv run celery -A main.celery_app worker --loglevel=info
```

Worker settings reuse the repository-level `.env` file (copy from `env.example`).

