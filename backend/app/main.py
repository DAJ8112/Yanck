"""Application entrypoint for FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure a :class:`FastAPI` instance."""

    application = FastAPI(title=settings.app_name, debug=settings.debug)
    
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_app()


