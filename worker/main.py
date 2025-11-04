"""Celery worker entry point."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "rag_worker",
    broker=settings.broker_url,
    backend=settings.backend_url,
)
celery_app.config_from_object(
    {
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
    }
)


def main() -> None:
    """Provide a direct CLI to run the Celery worker."""

    celery_app.worker_main()


if __name__ == "__main__":
    main()
