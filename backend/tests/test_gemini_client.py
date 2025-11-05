from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.providers import gemini as gemini_module
from app.services.providers.gemini import GeminiClient


@pytest.mark.asyncio
async def test_gemini_client_returns_text(monkeypatch) -> None:
    def fake_configure(*, api_key: str) -> None:  # noqa: ARG001 - testing stub
        assert api_key == "test-key"

    class FakeGenerativeModel:
        def __init__(self, **kwargs):  # noqa: D401 - simple stub
            self.kwargs = kwargs

        def generate_content(self, contents):
            return SimpleNamespace(text="assistant reply", candidates=[])

    fake_genai = SimpleNamespace(
        configure=fake_configure,
        GenerativeModel=lambda **kwargs: FakeGenerativeModel(**kwargs),
    )

    monkeypatch.setattr(gemini_module, "genai", fake_genai)

    client = GeminiClient(api_key="test-key", model="models/unit-test")
    response = await client.generate(system_prompt="sys", messages=[("user", "hello")])

    assert response == "assistant reply"

