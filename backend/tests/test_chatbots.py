from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import status

from app.main import app
from app.models import Document, DocumentStatus
from app.services.storage import get_storage_service


class InMemoryStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def upload_fileobj(
        self,
        fileobj,
        key: str,
        *,
        content_type: str | None = None,
        extra_args: dict | None = None,
    ) -> None:
        self.files[key] = fileobj.read()

    async def download_file(self, key: str, destination: Path) -> Path:
        destination.write_bytes(self.files[key])
        return destination

    async def delete_object(self, key: str) -> None:
        self.files.pop(key, None)


@pytest.mark.asyncio
async def test_create_chatbot_and_upload_document(async_client, db_session, monkeypatch) -> None:
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage_service] = lambda: storage
    monkeypatch.setattr(
        "app.core.celery.enqueue_document_ingestion",
        lambda document_id: None,
    )
    monkeypatch.setattr(
        "app.api.routes.chatbots.enqueue_document_ingestion",
        lambda document_id: None,
    )

    register_payload = {"email": "bob@example.com", "password": "password123", "full_name": "Bob"}
    await async_client.post("/api/auth/register", json=register_payload)

    login = await async_client.post(
        "/api/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    chatbot_payload = {
        "name": "Support Bot",
        "model_provider": "local",
        "model_name": "mini",
        "system_prompt": "Be helpful.",
        "temperature": 0.1,
        "top_k": 3,
    }
    response = await async_client.post("/api/chatbots", json=chatbot_payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    chatbot_data = response.json()
    chatbot_id = UUID(chatbot_data["id"])

    upload_response = await async_client.post(
        f"/api/chatbots/{chatbot_id}/documents",
        headers=headers,
        files={"files": ("example.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )

    assert upload_response.status_code == status.HTTP_200_OK
    documents = upload_response.json()
    assert len(documents) == 1
    assert documents[0]["status"] == DocumentStatus.PENDING.value

    stored_document = await db_session.get(Document, UUID(documents[0]["id"]))
    assert stored_document is not None
    assert stored_document.status == DocumentStatus.PENDING
    assert stored_document.size_bytes == len(b"Hello world")

    app.dependency_overrides.pop(get_storage_service, None)
