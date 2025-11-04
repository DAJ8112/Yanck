"""Embedding generation utilities with graceful fallbacks."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Iterable

try:  # pragma: no cover - optional heavy dependency
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:  # pragma: no cover - offline fallback
    SentenceTransformer = None


class EmbeddingService:
    """Generate vector representations for text snippets."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", normalize: bool = True) -> None:
        self.normalize = normalize
        if SentenceTransformer is not None:  # pragma: no cover - network dependent
            self._model = SentenceTransformer(model_name)
        else:
            self._model = None

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        items = list(texts)
        if not items:
            return []

        if self._model is not None:  # pragma: no cover - heavy path
            embeddings = self._model.encode(
                items, normalize_embeddings=self.normalize
            )
            return embeddings.tolist()

        return [self._fallback_embedding(text) for text in items]

    def embed_query(self, text: str) -> list[float]:
        if self._model is not None:  # pragma: no cover - heavy path
            vector = self._model.encode(
                [text], normalize_embeddings=self.normalize
            )[0]
            return vector.tolist()
        return self._fallback_embedding(text)

    @staticmethod
    def _fallback_embedding(text: str, dimensions: int = 48) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()
        seed = int(digest[:16], 16)
        rng = random.Random(seed)  # noqa: S311 - deterministic fallback for environments without embeddings
        return [rng.random() for _ in range(dimensions)]

