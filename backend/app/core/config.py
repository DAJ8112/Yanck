"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration for the backend service."""

    # Core application
    app_name: str = "RAG Builder API"
    environment: str = "dev"
    api_prefix: str = "/api"
    debug: bool = True

    # Security
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    jwt_algorithm: str = "HS256"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/rag"

    # Storage (S3-compatible)
    s3_endpoint_url: str = "http://minio:9000"
    s3_bucket_name: str = "rag-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"

    # Queue & cache
    redis_url: str = "redis://redis:6379/0"

    # Vector store (FAISS persistence directory)
    vector_store_path: Path = Path("./data/vector_store")

    # LLM providers
    gemini_api_key: str = ""
    gemini_model: str = "models/gemini-2.5-flash"
    gemini_safety_settings: str | None = None
    rag_top_k: int = 4

    # Model provider defaults
    default_model_provider: str = "gemini"
    default_model_name: str = "models/gemini-2.5-flash"

    @property
    def sync_database_url(self) -> str:
        """Return a synchronous-compatible SQLAlchemy database URL."""

        if "+asyncpg" in self.database_url:
            return self.database_url.replace("+asyncpg", "")
        return self.database_url

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of :class:`Settings`."""

    config = Settings()
    config.vector_store_path = config.vector_store_path.expanduser().resolve()
    config.vector_store_path.mkdir(parents=True, exist_ok=True)
    return config


settings = get_settings()


