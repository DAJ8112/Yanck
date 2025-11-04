# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG No-Code Platform - a monorepo for building Retrieval-Augmented Generation chatbots without code. The system consists of three main services:

- **backend/**: FastAPI REST API with async SQLAlchemy, JWT auth, and RAG orchestration
- **worker/**: Celery worker handling document ingestion, chunking, embeddings, and vector indexing
- **frontend/**: React + TypeScript dashboard built with Vite

## Common Commands

### Full Stack (Docker Compose)
```bash
# Start all services (Postgres, Redis, MinIO, backend, worker, frontend)
docker compose up --build

# Access points:
# - Backend API docs: http://localhost:8000/docs
# - Frontend: http://localhost:5173
# - MinIO console: http://localhost:9001 (minioadmin/minioadmin)
```

### Backend (FastAPI)
```bash
cd backend

# Install dependencies
uv sync

# Run locally
uv run uvicorn app.main:app --reload

# Lint
uv run ruff check .

# Type check
uv run mypy app

# Test
uv run pytest
uv run pytest --cov  # with coverage

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1
```

### Worker (Celery)
```bash
cd worker

# Install dependencies
uv sync

# Run worker locally
uv run celery -A main.celery_app worker --loglevel=info

# Run with specific concurrency
uv run celery -A main.celery_app worker --loglevel=info --concurrency=2

# Lint, type check, test (same as backend)
uv run ruff check .
uv run mypy app
uv run pytest
```

### Frontend (React + Vite)
```bash
cd frontend

# Install dependencies
npm install

# Dev server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
npm run lint -- --max-warnings=0

# Preview production build
npm run preview
```

## Architecture

### Document Ingestion Pipeline

1. **Upload**: User uploads document via API → stored in MinIO (S3-compatible storage)
2. **Queue**: Backend creates `Document` record with status=PENDING and dispatches Celery task
3. **Processing** (Worker):
   - Download file from MinIO
   - Extract text (supports PDF, TXT, etc.)
   - Chunk text into segments
   - Generate embeddings using EmbeddingService
   - Store chunks and embeddings in Postgres
   - Add embeddings to FAISS vector index
   - Update Document status to READY
4. **Query**: When chatbot receives query, embeddings are used to retrieve relevant chunks from FAISS, then sent to LLM

### Data Model

Core entities (app/models/):
- **User**: Authentication and ownership
- **Chatbot**: Configuration (name, slug, model, temperature, top_k, system_prompt)
- **Document**: Uploaded files with status tracking (PENDING → PROCESSING → READY/FAILED)
- **Chunk**: Text segments split from documents
- **Embedding**: Vector representations of chunks (stored as JSON arrays)
- **Conversation**: Chat sessions
- **UsageLog**: Token/cost tracking

Relationships:
- User → owns many Chatbots
- Chatbot → has many Documents, Chunks, Conversations
- Document → has many Chunks
- Chunk → has one Embedding

### Vector Storage

- Uses FAISS for similarity search (file-based persistence)
- Vector store location: `./data/vector_store` (configurable via `VECTOR_STORE_PATH`)
- Each chatbot has its own FAISS index (keyed by chatbot_id)
- Embeddings are also stored in Postgres for auditability

### Configuration

All services use environment variables from `.env` (copy from `env.example`):
- Database: PostgreSQL with asyncpg driver
- Cache/Queue: Redis (separate DBs for caching and Celery)
- Storage: MinIO (S3-compatible)
- Models: Configurable provider (default: Ollama with llama3)

Backend and worker use Pydantic Settings (app/core/config.py, worker/app/core/config.py) to load and validate configuration.

### Shared Code

Backend and worker share:
- Database models (backend/app/models/)
- Services (storage, embeddings, text extraction, vector store)
- Configuration schema

Worker imports from backend:
```python
from backend.app.db.session import SessionLocal
from backend.app.models import Chunk, Document, Embedding
from backend.app.services import EmbeddingService, S3StorageService, VectorStore
```

### API Structure

- Routes: app/api/routes/ (auth.py, chatbots.py, health.py)
- All routes prefixed with `/api` (configurable via `API_PREFIX`)
- FastAPI automatic docs at `/docs`
- JWT authentication with access/refresh tokens

### Testing

- Backend/Worker: pytest with async support (pytest-asyncio)
- Uses in-memory SQLite for test database (aiosqlite)
- Coverage reporting available via pytest-cov

## Development Workflow

1. **Make changes** in appropriate service directory
2. **Run service-specific linting/tests** to catch issues early:
   ```bash
   uv run ruff check .
   uv run mypy app
   uv run pytest
   ```
3. **Test in Docker** if changes affect service integration:
   ```bash
   docker compose up --build
   ```
4. **Migrations**: If models change, create migration in backend/:
   ```bash
   uv run alembic revision --autogenerate -m "description"
   ```

## Dependencies

- Python: 3.11+ (managed with uv, not pip)
- Node.js: 20+
- Database: PostgreSQL 16
- Cache/Queue: Redis 7
- Storage: MinIO (or any S3-compatible service)

Python key libraries:
- FastAPI, Uvicorn: Web framework and ASGI server
- SQLAlchemy 2.0+: Async ORM
- Alembic: Database migrations
- Celery: Background task queue
- boto3: S3 interactions
- FAISS (via langchain or direct): Vector similarity search
- Pydantic: Data validation and settings
- Ruff: Linting (replaces flake8, isort, etc.)
- mypy: Type checking
