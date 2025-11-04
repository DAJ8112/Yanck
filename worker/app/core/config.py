"""Settings for Celery worker."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "dev"
    broker_url: str = Field("redis://redis:6379/0", alias="CELERY_BROKER_URL")
    backend_url: str = Field("redis://redis:6379/1", alias="CELERY_BACKEND_URL")
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/rag"
    s3_endpoint_url: str = "http://minio:9000"
    s3_bucket_name: str = "rag-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    vector_store_path: Path = Path("./data/vector_store")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    config = Settings()
    config.vector_store_path = config.vector_store_path.expanduser().resolve()
    config.vector_store_path.mkdir(parents=True, exist_ok=True)
    return config


settings = get_settings()


