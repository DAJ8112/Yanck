"""Chat-specific API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models import Conversation, Message, MessageRole, User
from app.schemas import ChatRequest, ChatResponse, ChatContextChunk, ChatMessage, DocumentRead
from app.services import ChatbotService, DocumentService, RAGService
from app.services.rag import RAGGenerationError


router = APIRouter(prefix="/chatbots", tags=["chat"])


@router.get("/{chatbot_id}/documents", response_model=list[DocumentRead])
async def list_chatbot_documents(
    chatbot_id: UUID,
    current_user: User = Depends(deps.get_current_active_user),
    session: AsyncSession = Depends(deps.get_db),
):
    chatbot_service = ChatbotService(session)
    await chatbot_service.ensure_owner(chatbot_id, current_user.id)

    document_service = DocumentService(session)
    documents = await document_service.list_for_chatbot(chatbot_id, current_user.id)
    return [DocumentRead.model_validate(document) for document in documents]


@router.post("/{chatbot_id}/chat", response_model=ChatResponse)
async def chat_with_bot(
    chatbot_id: UUID,
    payload: ChatRequest,
    current_user: User = Depends(deps.get_current_active_user),
    session: AsyncSession = Depends(deps.get_db),
):
    chatbot_service = ChatbotService(session)
    chatbot = await chatbot_service.ensure_owner(chatbot_id, current_user.id)

    conversation, created_new_conversation = await _get_or_create_conversation(
        session, chatbot_id, current_user.id, payload.conversation_id
    )

    clean_message = payload.message.strip()
    if not clean_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    history = await _load_history(session, conversation.id)

    rag_service = RAGService(session)
    try:
        rag_result = await rag_service.generate_response(
            chatbot,
            clean_message,
            history=history,
            top_k=payload.top_k,
        )
    except RAGGenerationError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=clean_message,
    )
    session.add(user_message)

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=rag_result.answer,
    )
    session.add(assistant_message)

    if created_new_conversation and not conversation.title:
        conversation.title = clean_message[:120]

    try:
        await session.commit()
    except Exception as exc:  # pragma: no cover - defensive, logged upstream
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist chat messages",
        ) from exc

    await session.refresh(assistant_message)

    context_chunks = [
        ChatContextChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            document_name=chunk.document_name,
            score=chunk.score,
            content=chunk.content,
        )
        for chunk in rag_result.chunks
    ]

    reply = ChatMessage.model_validate(assistant_message)
    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply,
        context=context_chunks,
        created_new_conversation=created_new_conversation,
    )


async def _get_or_create_conversation(
    session: AsyncSession,
    chatbot_id: UUID,
    owner_id: UUID,
    conversation_id: UUID | None,
) -> tuple[Conversation, bool]:
    if conversation_id is not None:
        conversation = await session.get(Conversation, conversation_id)
        if (
            conversation is None
            or conversation.chatbot_id != chatbot_id
            or conversation.user_id != owner_id
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return conversation, False

    conversation = Conversation(chatbot_id=chatbot_id, user_id=owner_id)
    session.add(conversation)
    await session.flush()
    return conversation, True


async def _load_history(
    session: AsyncSession, conversation_id: UUID
) -> list[tuple[str, str]]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()
    return [(message.role.value, message.content) for message in messages]

