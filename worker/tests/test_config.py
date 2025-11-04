from app.core.config import settings


def test_settings_load() -> None:
    assert settings.broker_url.startswith("redis://")

