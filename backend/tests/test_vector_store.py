from __future__ import annotations

from uuid import uuid4

from app.services.vector_store import VectorStore


def test_similarity_search_returns_best_match(tmp_path) -> None:
    chatbot_id = uuid4()
    store = VectorStore(tmp_path, chatbot_id, dimension=3)

    primary_chunk = str(uuid4())
    secondary_chunk = str(uuid4())

    store.add_embeddings(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        [primary_chunk, secondary_chunk],
    )

    results = store.similarity_search([0.9, 0.1, 0.0], top_k=2)

    assert results, "Expected at least one similarity search result"
    top_chunk_id, score = results[0]
    assert top_chunk_id == primary_chunk
    assert score > 0.0

