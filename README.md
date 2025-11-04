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

See per-service `README.md` files for service-specific commands.

