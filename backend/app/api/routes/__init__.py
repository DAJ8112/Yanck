"""API route registration module."""

from fastapi import APIRouter

from app.api.routes import auth, chat, chatbots, health

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(chatbots.router)
router.include_router(chat.router)

