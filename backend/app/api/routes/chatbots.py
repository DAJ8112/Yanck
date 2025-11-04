"""Chatbot management and document ingestion endpoints."""

from __future__ import annotations

import hashlib
import io
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api import deps
from app.core.celery import enqueue_document_ingestion
from app.models import User
from app.schemas import ChatbotCreate, ChatbotRead, DocumentRead
from app.services import (
    ChatbotService,
    DocumentService,
    S3StorageService,
    get_storage_service,
)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


router = APIRouter(prefix="/chatbots", tags=["chatbots"])


@router.post("", response_model=ChatbotRead, status_code=status.HTTP_201_CREATED)
async def create_chatbot(
    payload: ChatbotCreate,
    current_user: User = Depends(deps.get_current_active_user),
    session=Depends(deps.get_db),
):
    service = ChatbotService(session)
    chatbot = await service.create(current_user, payload)
    return ChatbotRead.model_validate(chatbot)


@router.get("", response_model=list[ChatbotRead])
async def list_chatbots(
    current_user: User = Depends(deps.get_current_active_user),
    session=Depends(deps.get_db),
):
    service = ChatbotService(session)
    chatbots = await service.list_for_user(current_user.id)
    return [ChatbotRead.model_validate(item) for item in chatbots]


@router.get("/{chatbot_id}", response_model=ChatbotRead)
async def get_chatbot(
    chatbot_id: UUID,
    current_user: User = Depends(deps.get_current_active_user),
    session=Depends(deps.get_db),
):
    service = ChatbotService(session)
    chatbot = await service.get_for_user(chatbot_id, current_user.id)
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return ChatbotRead.model_validate(chatbot)


@router.post("/{chatbot_id}/documents", response_model=list[DocumentRead])
async def upload_documents(
    chatbot_id: UUID,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(deps.get_current_active_user),
    session=Depends(deps.get_db),
    storage: S3StorageService = Depends(get_storage_service),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

    chatbot_service = ChatbotService(session)
    chatbot = await chatbot_service.ensure_owner(chatbot_id, current_user.id)

    document_service = DocumentService(session)
    created_documents: list[DocumentRead] = []

    for upload in files:
        contents = await upload.read()
        size = len(contents)
        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"File {upload.filename} is empty"
            )
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {upload.filename} exceeds the 50MB limit",
            )

        checksum = hashlib.sha256(contents).hexdigest()
        storage_key = _build_storage_key(current_user.id, chatbot.id, upload.filename)
        await storage.upload_fileobj(
            io.BytesIO(contents),
            storage_key,
            content_type=upload.content_type or "application/octet-stream",
        )

        document = await document_service.create_document(
            chatbot_id=chatbot.id,
            uploader_id=current_user.id,
            file_name=upload.filename,
            storage_path=storage_key,
            mime_type=upload.content_type or "application/octet-stream",
            size_bytes=size,
            checksum=checksum,
        )

        enqueue_document_ingestion(str(document.id))
        created_documents.append(DocumentRead.model_validate(document))

    return created_documents


def _build_storage_key(user_id: UUID, chatbot_id: UUID, filename: str) -> str:
    sanitized = filename.replace(" ", "_")
    return f"users/{user_id}/{chatbot_id}/{uuid4().hex}_{sanitized}"

