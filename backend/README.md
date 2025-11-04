# Backend Service

FastAPI-based API for the RAG no-code platform. Uses uv for dependency management and ships with async SQLAlchemy, Redis, Celery, and S3 integrations.

## Setup

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Environment variables are configured via a project-level `.env` file (see `env.example` at the repository root for defaults).

