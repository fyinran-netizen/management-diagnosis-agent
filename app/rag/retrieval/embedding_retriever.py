from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from app.rag.embeddings import embed_query
from app.rag.vector_store import chunk_to_embedding_text, load_vector_index


@lru_cache(maxsize=1)
def get_cached_vector_index() -> tuple[tuple[dict[str, Any], ...], np.ndarray, dict[str, Any]]:
    chunks, embeddings, metadata = load_vector_index()
    return tuple(chunks), embeddings, metadata


def retrieve_by_embedding(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    chunks, embeddings, _metadata = get_cached_vector_index()
    if not chunks:
        return []

    query_embedding = embed_query(query)
    scores = embeddings @ query_embedding
    top_indices = np.argsort(scores)[::-1][:top_k]

    results: list[dict[str, Any]] = []
    for index in top_indices:
        chunk = dict(chunks[int(index)])
        score = float(scores[int(index)])
        chunk["score"] = score
        chunk["embedding_score"] = score
        chunk["retrieval_method"] = "embedding"
        chunk["embedding_text"] = chunk_to_embedding_text(chunk)
        results.append(chunk)

    return results
