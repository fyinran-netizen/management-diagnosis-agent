from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from app.tools.retrieval.embeddings import embed_query
from app.tools.retrieval.schemas import RetrievedChunk
from app.tools.retrieval.vector_store import VECTOR_INDEX_DIR, chunk_to_embedding_text, load_vector_index


@lru_cache(maxsize=4)
def get_cached_vector_index(index_dir: Path = VECTOR_INDEX_DIR) -> tuple[tuple[dict[str, Any], ...], np.ndarray, dict[str, Any]]:
    chunks, embeddings, metadata = load_vector_index(index_dir)
    return tuple(chunks), embeddings, metadata


def retrieve_by_embedding(query: str, top_k: int = 5, index_dir: Path = VECTOR_INDEX_DIR) -> list[RetrievedChunk]:
    chunks, embeddings, _metadata = get_cached_vector_index(index_dir)
    if not chunks:
        return []
    scores = embeddings @ embed_query(query)
    indices = np.argsort(scores)[::-1][:top_k]
    results: list[RetrievedChunk] = []
    for index in indices:
        chunk: RetrievedChunk = dict(chunks[int(index)])
        score = float(scores[int(index)])
        rank = len(results) + 1
        chunk.update(
            score=score,
            embedding_score=score,
            embedding_cosine_score=score,
            retrieval_method="embedding",
            rank=rank,
            embedding_rank=rank,
            embedding_text=chunk_to_embedding_text(chunk),
        )
        results.append(chunk)
    return results
