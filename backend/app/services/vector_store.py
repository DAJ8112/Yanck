"""Vector store utilities backed by FAISS when available."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

import numpy as np

try:  # pragma: no cover - optional dependency
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - fallback path
    faiss = None


class VectorStore:
    """Persist embeddings for a chatbot using FAISS or numpy fallback."""

    def __init__(self, base_path: Path, chatbot_id: UUID, dimension: int) -> None:
        self.base_path = base_path
        self.chatbot_id = chatbot_id
        self.dimension = dimension
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.index_path = self.base_path / f"{chatbot_id}.faiss"
        self.meta_path = self.base_path / f"{chatbot_id}.json"
        self.matrix_path = self.base_path / f"{chatbot_id}.npy"

        self.metadata: dict[str, list[str] | int] = {"chunk_ids": [], "dimension": dimension}
        if self.meta_path.exists():
            with self.meta_path.open("r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            self.metadata.update(loaded)

        self._index = None
        self._matrix: np.ndarray | None = None

        if faiss is not None and self.index_path.exists():  # pragma: no cover - requires faiss
            self._index = faiss.read_index(str(self.index_path))
        elif self.matrix_path.exists():
            self._matrix = np.load(self.matrix_path)

    def add_embeddings(self, embeddings: Iterable[list[float]], chunk_ids: Iterable[str]) -> None:
        vectors = np.array(list(embeddings), dtype="float32")
        ids = list(chunk_ids)
        if not len(vectors):
            return

        if vectors.shape[1] != self.dimension:
            raise ValueError("Embedding dimension mismatch for vector store")

        if faiss is not None:  # pragma: no cover - optional heavy dependency
            if self._index is None:
                self._index = faiss.IndexFlatIP(self.dimension)
            self._index.add(vectors)
            faiss.write_index(self._index, str(self.index_path))
        else:
            if self._matrix is None:
                self._matrix = vectors
            else:
                self._matrix = np.vstack([self._matrix, vectors])
            np.save(self.matrix_path, self._matrix)

        existing_ids: list[str] = list(self.metadata.get("chunk_ids", []))
        existing_ids.extend(ids)
        self.metadata["chunk_ids"] = existing_ids
        self.metadata["dimension"] = self.dimension
        with self.meta_path.open("w", encoding="utf-8") as fh:
            json.dump(self.metadata, fh)



