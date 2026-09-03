from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from app.tools.retrieval.embeddings import embed_query
from app.tools.retrieval.vector_store import (
    SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
    chunk_to_embedding_text,
    load_vector_index,
)


@lru_cache(maxsize=1)
def get_cached_vector_index_metadata() -> tuple[
    tuple[dict[str, Any], ...], np.ndarray, dict[str, Any]
]:
    chunks, embeddings, metadata = load_vector_index(
        SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR
    )
    return tuple(chunks), embeddings, metadata


def retrieve_by_embedding_metadata(
    query: str, top_k: int = 5
) -> list[dict[str, Any]]:
    """Retrieve using vectors built from chunk text plus unweighted metadata."""
    chunks, embeddings, _metadata = get_cached_vector_index_metadata()
    if not chunks:
        return []

    query_embedding = embed_query(query)
    scores = embeddings @ query_embedding
    top_indices = np.argsort(scores)[::-1][:top_k]

    results: list[dict[str, Any]] = []
    for index in top_indices:
        chunk = dict(chunks[int(index)])
        score = float(scores[int(index)])
        rank = len(results) + 1
        chunk["score"] = score
        chunk["embedding_score"] = score
        chunk["embedding_cosine_score"] = score
        chunk["retrieval_method"] = "embedding_metadata"
        chunk["rank"] = rank
        chunk["embedding_rank"] = rank
        chunk["embedding_text"] = chunk_to_embedding_text(chunk)
        results.append(chunk)

    return results
