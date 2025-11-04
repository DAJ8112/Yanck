"""API route registration module."""

from fastapi import APIRouter

from app.api.routes import auth, chatbots, health

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(chatbots.router)

