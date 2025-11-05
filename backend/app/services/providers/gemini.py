"""Google Gemini model client wrapper."""

from __future__ import annotations

import asyncio
from typing import Any, Sequence

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai
    from google.api_core.exceptions import GoogleAPIError
except ImportError as exc:  # pragma: no cover - dependency optional during testing
    genai = None  # type: ignore[assignment]

    class GoogleAPIError(Exception):  # type: ignore[no-redef]
        """Fallback exception type when google-api-core is unavailable."""

        pass


class GeminiProviderError(RuntimeError):
    """Raised when the Gemini provider cannot fulfill a request."""


class GeminiClient:
    """Thin async wrapper around the Google Generative AI client."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        safety_settings: Sequence[dict[str, Any]] | None = None,
        generation_config: dict[str, Any] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required but was not provided.")
        if not model:
            raise ValueError("A Gemini model name must be supplied.")
        if genai is None:  # pragma: no cover - handled in tests via monkeypatch
            raise ImportError(
                "google-generativeai is not installed. Run `uv sync` to install dependencies."
            )

        genai.configure(api_key=api_key)

        self._model_name = model
        self._safety_settings = list(safety_settings or []) or None
        self._generation_config = generation_config or None

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[tuple[str, str]],
        generation_config: dict[str, Any] | None = None,
    ) -> str:
        """Generate a response from Gemini for the supplied conversation history."""

        def _invoke() -> str:
            model = genai.GenerativeModel(  # type: ignore[union-attr]
                model_name=self._model_name,
                system_instruction=system_prompt or None,
                generation_config=generation_config or self._generation_config,
                safety_settings=self._safety_settings,
            )

            contents = [
                {
                    "role": role,
                    "parts": [
                        {"text": content},
                    ],
                }
                for role, content in messages
            ]

            response = model.generate_content(contents)

            text = getattr(response, "text", None)
            if text:
                return str(text).strip()

            # Fallback: search through candidates/parts for textual content.
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                if not content:
                    continue
                parts = getattr(content, "parts", None)
                if not parts:
                    continue
                for part in parts:
                    value = getattr(part, "text", None)
                    if value:
                        return str(value).strip()
                    if isinstance(part, dict) and part.get("text"):
                        return str(part["text"]).strip()

            raise GeminiProviderError("Gemini returned an empty response")

        try:
            return await asyncio.to_thread(_invoke)
        except GoogleAPIError as exc:  # pragma: no cover - network failure path
            raise GeminiProviderError("Gemini API error") from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise GeminiProviderError("Gemini generation failed") from exc

