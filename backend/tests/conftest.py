from __future__ import annotations

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Configure an isolated SQLite database for tests before importing app modules.
test_db_path = Path("tests/test.db").resolve()
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{test_db_path}")

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def prepare_database() -> None:
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture(autouse=True)
async def clean_database() -> None:
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def async_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session

