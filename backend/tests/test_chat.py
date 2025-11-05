from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.models import Document, DocumentStatus, Message, MessageRole, User
from app.services.rag import RAGResponse, RetrievedChunk


async def _register_and_login(async_client, db_session, email: str, password: str) -> tuple[dict[str, str], UUID]:
    payload = {"email": email, "password": password, "full_name": "Test User"}
    await async_client.post("/api/auth/register", json=payload)

    login_response = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    tokens = login_response.json()

    user = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers, user.id


@pytest.mark.asyncio
async def test_list_chatbot_documents(async_client, db_session) -> None:
    headers, user_id = await _register_and_login(async_client, db_session, "doc@example.com", "password123")

    chatbot_payload = {
        "name": "Support Bot",
        "model_provider": "local",
        "model_name": "mini",
        "system_prompt": "Be helpful.",
        "temperature": 0.2,
        "top_k": 3,
    }
    chatbot_response = await async_client.post("/api/chatbots", json=chatbot_payload, headers=headers)
    chatbot_id = UUID(chatbot_response.json()["id"])

    document = Document(
        id=uuid4(),
        chatbot_id=chatbot_id,
        uploaded_by=user_id,
        file_name="handbook.txt",
        file_path="users/documents/handbook.txt",
        mime_type="text/plain",
        size_bytes=128,
        status=DocumentStatus.READY,
    )
    db_session.add(document)
    await db_session.commit()

    response = await async_client.get(f"/api/chatbots/{chatbot_id}/documents", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["file_name"] == "handbook.txt"


@pytest.mark.asyncio
async def test_chat_endpoint_creates_conversation(async_client, db_session, monkeypatch) -> None:
    headers, user_id = await _register_and_login(async_client, db_session, "chat@example.com", "password123")

    chatbot_payload = {
        "name": "Guide Bot",
        "model_provider": "local",
        "model_name": "mini",
        "system_prompt": "Assist users.",
        "temperature": 0.2,
        "top_k": 3,
    }
    chatbot_response = await async_client.post("/api/chatbots", json=chatbot_payload, headers=headers)
    chatbot_id = UUID(chatbot_response.json()["id"])

    doc_id = uuid4()
    db_session.add(
        Document(
            id=doc_id,
            chatbot_id=chatbot_id,
            uploaded_by=user_id,
            file_name="faq.txt",
            file_path="users/documents/faq.txt",
            mime_type="text/plain",
            size_bytes=64,
            status=DocumentStatus.READY,
        )
    )
    await db_session.commit()

    chunk_id = uuid4()

    async def fake_generate_response(self, chatbot, user_message, *, history=None, top_k=None):  # noqa: ANN001
        return RAGResponse(
            answer="Hello!",
            chunks=[
                RetrievedChunk(
                    id=chunk_id,
                    document_id=doc_id,
                    document_name="faq.txt",
                    score=0.95,
                    content="Sample chunk content.",
                )
            ],
        )

    monkeypatch.setattr("app.api.routes.chat.RAGService.generate_response", fake_generate_response)

    response = await async_client.post(
        f"/api/chatbots/{chatbot_id}/chat",
        json={"message": "How do I reset my password?"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert UUID(body["conversation_id"])
    assert body["created_new_conversation"] is True
    assert body["reply"]["content"] == "Hello!"
    assert body["context"][0]["document_name"] == "faq.txt"

    conversation_id = UUID(body["conversation_id"])
    messages = (
        await db_session.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        )
    ).scalars().all()

    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[1].role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_chat_endpoint_rejects_unknown_conversation(async_client, db_session, monkeypatch) -> None:
    headers, _ = await _register_and_login(async_client, db_session, "missing@example.com", "password123")

    chatbot_payload = {
        "name": "Help Bot",
        "model_provider": "local",
        "model_name": "mini",
        "system_prompt": "Assist users.",
        "temperature": 0.2,
        "top_k": 3,
    }
    chatbot_response = await async_client.post("/api/chatbots", json=chatbot_payload, headers=headers)
    chatbot_id = UUID(chatbot_response.json()["id"])

    async def fake_generate_response(*args, **kwargs):  # noqa: ANN001
        raise AssertionError("RAGService should not be invoked for missing conversations")

    monkeypatch.setattr("app.api.routes.chat.RAGService.generate_response", fake_generate_response)

    response = await async_client.post(
        f"/api/chatbots/{chatbot_id}/chat",
        json={"message": "Hello", "conversation_id": str(uuid4())},
        headers=headers,
    )

    assert response.status_code == 404

