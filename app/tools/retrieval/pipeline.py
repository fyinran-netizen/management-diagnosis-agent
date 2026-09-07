from __future__ import annotations

import os

from app.tools.retrieval.rerankers.bge_reranker import rerank
from app.tools.retrieval.retrievers.hybrid_linear import hybrid_retrieve
from app.tools.retrieval.schemas import RetrievedChunk


DEFAULT_CANDIDATE_MULTIPLIER = int(os.getenv("RERANKER_CANDIDATE_MULTIPLIER", "5"))
DEFAULT_MIN_CANDIDATES = int(os.getenv("RERANKER_MIN_CANDIDATES", "25"))


def retrieve_pipeline(
    query: str,
    *,
    candidate_top_k: int | None = None,
    final_top_k: int = 5,
    use_reranker: bool = True,
) -> list[RetrievedChunk]:
    """Run hybrid candidate retrieval followed by the optional reranker."""
    if final_top_k <= 0:
        return []

    candidate_k = candidate_top_k or max(
        final_top_k * DEFAULT_CANDIDATE_MULTIPLIER,
        DEFAULT_MIN_CANDIDATES,
    )
    candidate_k = max(candidate_k, final_top_k)
    candidates = hybrid_retrieve(query=query, top_k=candidate_k)

    if not use_reranker or not candidates:
        return candidates[:final_top_k]
    return rerank(query=query, candidates=candidates, top_k=final_top_k)
