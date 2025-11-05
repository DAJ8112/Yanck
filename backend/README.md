# Backend Service

FastAPI-based API for the RAG no-code platform. Uses uv for dependency management and ships with async SQLAlchemy, Redis, Celery, and S3 integrations.

## Setup

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Environment variables are configured via a project-level `.env` file (see `env.example` at the repository root for defaults).

### Retrieval & Generation Configuration

- `GEMINI_API_KEY` – Google Gemini API key
- `GEMINI_MODEL` – Gemini model identifier (defaults to `models/gemini-2.5-flash`)
- `GEMINI_SAFETY_SETTINGS` – Optional JSON array of safety settings forwarded to the Gemini client
- `RAG_TOP_K` – Default number of chunks to retrieve from the vector store for each query

### Chat Endpoints

- `GET /api/chatbots/{chatbot_id}/documents` – list uploaded documents with status metadata
- `POST /api/chatbots/{chatbot_id}/chat` – persist a conversation turn, run retrieval-augmented generation, and return the assistant reply alongside the supporting context chunks

Both endpoints require a valid bearer token obtained via the auth routes (`/api/auth/login`).

