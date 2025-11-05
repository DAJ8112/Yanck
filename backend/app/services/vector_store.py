"""Vector store utilities backed by FAISS when available."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
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

        stored_dimension = self.metadata.get("dimension")
        if isinstance(stored_dimension, int) and stored_dimension > 0:
            self.dimension = stored_dimension

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

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 4
    ) -> list[tuple[str, float]]:
        """Return the most relevant chunk ids ranked by similarity."""

        if top_k <= 0:
            return []

        query = np.asarray(query_embedding, dtype="float32")
        if query.ndim != 1:
            raise ValueError("Query embedding must be a 1-D vector")
        if query.shape[0] != self.dimension:
            raise ValueError("Query embedding dimension mismatch for vector store")

        chunk_ids = list(self.metadata.get("chunk_ids", []))
        if not chunk_ids:
            return []

        if self._use_faiss:
            return self._faiss_search(query, chunk_ids, top_k)

        matrix = self._ensure_matrix()
        if matrix.size == 0:
            return []

        if matrix.shape[1] != query.shape[0]:
            raise ValueError("Stored embedding dimension mismatch for vector store")

        if matrix.shape[0] != len(chunk_ids):
            raise ValueError("Vector store metadata is out of sync with stored embeddings")

        similarities = matrix @ query
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [
            (chunk_ids[index], float(similarities[index]))
            for index in top_indices
        ]

    @property
    def _use_faiss(self) -> bool:
        return faiss is not None and self._index is not None

    def _ensure_matrix(self) -> np.ndarray:
        if self._matrix is None and self.matrix_path.exists():
            self._matrix = np.load(self.matrix_path).astype("float32")
        if self._matrix is None:
            self._matrix = np.empty((0, self.dimension), dtype="float32")
        return self._matrix

    def _faiss_search(
        self, query: np.ndarray, chunk_ids: list[str], top_k: int
    ) -> list[tuple[str, float]]:
        if self._index is None:
            return []

        query_batch = np.expand_dims(query, axis=0)
        scores, indices = self._index.search(query_batch, top_k)
        if scores.size == 0:
            return []

        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if idx >= len(chunk_ids):
                continue
            results.append((chunk_ids[idx], float(score)))
        return results




