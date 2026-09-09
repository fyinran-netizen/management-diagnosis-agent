from __future__ import annotations

import os

from app.tools.retrieval.rerankers.bge_reranker import score_candidates
from app.tools.retrieval.retrievers.hybrid_linear import hybrid_retrieve
from app.tools.retrieval.schemas import RetrievedChunk


DEFAULT_CANDIDATE_MULTIPLIER = int(os.getenv("RERANKER_CANDIDATE_MULTIPLIER", "5"))
DEFAULT_MIN_CANDIDATES = int(os.getenv("RERANKER_MIN_CANDIDATES", "25"))


def retrieve_pipeline(
    query: str,
    *,
    mode: str = "hybrid_rerank",
    hybrid_candidate_k: int | None = None,
    final_k: int = 5,
    source_retrieval_k: int | None = None,
) -> list[RetrievedChunk]:
    """Retrieve chunks using hybrid retrieval, optionally followed by reranking."""
    if mode not in {"hybrid", "hybrid_rerank"}:
        raise ValueError(f"Unsupported retrieval mode: {mode}")
    if final_k <= 0:
        return []

    if mode == "hybrid":
        return hybrid_retrieve(
            query=query,
            hybrid_top_k=final_k,
            source_retrieval_k=source_retrieval_k,
        )

    candidate_k = (
        hybrid_candidate_k
        if hybrid_candidate_k is not None
        else max(final_k * DEFAULT_CANDIDATE_MULTIPLIER, DEFAULT_MIN_CANDIDATES)
    )
    candidates = hybrid_retrieve(
        query=query,
        hybrid_top_k=candidate_k,
        source_retrieval_k=source_retrieval_k,
    )

    scored_candidates = score_candidates(
        query=query,
        candidates=candidates,
    )

    results = sorted(
        scored_candidates,
        key=lambda item: float(item.get("rerank_score", 0.0)),
        reverse=True,
    )[:final_k]

    for rank, item in enumerate(results, 1):
        item["rank"] = rank
        item["score"] = float(item["rerank_score"])
        item["retrieval_method"] = "hybrid_rerank"

    return results
