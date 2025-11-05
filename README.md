# RAG No-Code Platform

Monorepo containing the FastAPI backend, Celery worker, and Vite React frontend for building Retrieval-Augmented Generation chatbots without writing code.

## Getting Started

1. Copy environment defaults:
   ```bash
   cp env.example .env
   ```
2. Start services:
   ```bash
   docker compose up --build
   ```
3. Access apps:
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:5173
   - MinIO Console: http://localhost:9001 (minioadmin / minioadmin)

## Project Layout

- `backend/` — FastAPI application (uv-managed)
- `worker/` — Celery ingestion workers (uv-managed)
- `frontend/` — React + TypeScript dashboard (Vite)
- `docker-compose.yml` — Local orchestration for Postgres, Redis, MinIO, API, worker, and frontend

## Development Tooling

- Python: uv, FastAPI, SQLAlchemy, Alembic
- Background tasks: Celery, Redis
- Storage: MinIO (S3-compatible)
- Frontend: Vite, React, TypeScript
- Testing/Linting: pytest, mypy, ruff, eslint, vitest

## RAG Chat API

1. Configure Gemini credentials in `.env`:
   ```bash
   GEMINI_API_KEY=your-google-gemini-key
   GEMINI_MODEL=models/gemini-2.5-flash
   RAG_TOP_K=4
   ```
2. Start the stack (`docker compose up --build`) and authenticate to obtain a bearer token.
3. Create a chatbot and upload documents, then invoke the chat endpoint:
   ```bash
   curl -X POST "http://localhost:8000/api/chatbots/<chatbot_id>/chat" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"message":"What does the handbook say about onboarding?"}'
   ```
   The response includes the assistant reply plus the context chunks that grounded the answer.

## Frontend Dashboard

1. Install dependencies and start the dev server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Visit http://localhost:5173 and paste a JWT access token into the header form. The token is stored in `localStorage` and automatically attached to API calls.
3. Create chatbots, upload documents from the detail view, and chat end-to-end against the RAG backend.
4. Run frontend checks with `npm run lint`, `npm run build`, and `npm run test` (Vitest + Testing Library).

See per-service `README.md` files for service-specific commands.

