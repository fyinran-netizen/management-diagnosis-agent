from __future__ import annotations

import os
from pathlib import Path

from app.core.config import (
    PRODUCTION_RETRIEVAL_BM25_METADATA_MODE,
    PRODUCTION_RETRIEVAL_CANDIDATE_K,
    PRODUCTION_RETRIEVAL_CORPUS_DIR,
    PRODUCTION_RETRIEVAL_EMBEDDING_INDEX_DIR,
)
from app.tools.retrieval.rerankers.bge_reranker import score_candidates
from app.tools.retrieval.retrievers.hybrid_linear import hybrid_retrieve
from app.tools.retrieval.retrievers.hybrid_rrf import hybrid_retrieve_rrf
from app.tools.retrieval.schemas import RetrievedChunk


DEFAULT_CANDIDATE_MULTIPLIER = int(os.getenv("RERANKER_CANDIDATE_MULTIPLIER", "5"))
DEFAULT_MIN_CANDIDATES = int(os.getenv("RERANKER_MIN_CANDIDATES", "25"))


def retrieve_pipeline(
    query: str,
    *,
    mode: str = "hybrid",
    hybrid_candidate_k: int | None = None,
    final_k: int = 5,
    source_retrieval_k: int | None = None,
    corpus_dir: Path | None = None,
    embedding_index_dir: Path | None = None,
    bm25_metadata_mode: str | None = None,
) -> list[RetrievedChunk]:
    """Retrieve chunks using hybrid retrieval, optionally followed by reranking."""
    if mode not in {"hybrid", "hybrid_rerank"}:
        raise ValueError(f"Unsupported retrieval mode: {mode}")
    if final_k <= 0:
        return []

    effective_corpus_dir = corpus_dir or PRODUCTION_RETRIEVAL_CORPUS_DIR
    effective_embedding_index_dir = (
        embedding_index_dir or PRODUCTION_RETRIEVAL_EMBEDDING_INDEX_DIR
    )
    effective_metadata_mode = (
        bm25_metadata_mode or PRODUCTION_RETRIEVAL_BM25_METADATA_MODE
    )
    effective_source_retrieval_k = source_retrieval_k or PRODUCTION_RETRIEVAL_CANDIDATE_K

    if mode == "hybrid":
        return hybrid_retrieve_rrf(
            query=query,
            top_k=final_k,
            source_retrieval_k=effective_source_retrieval_k,
            corpus_dir=effective_corpus_dir,
            embedding_index_dir=effective_embedding_index_dir,
            bm25_metadata_mode=effective_metadata_mode,
        )

    candidate_k = (
        hybrid_candidate_k
        if hybrid_candidate_k is not None
        else max(final_k * DEFAULT_CANDIDATE_MULTIPLIER, DEFAULT_MIN_CANDIDATES)
    )
    candidates = hybrid_retrieve_rrf(
        query=query,
        top_k=candidate_k,
        source_retrieval_k=effective_source_retrieval_k,
        corpus_dir=effective_corpus_dir,
        embedding_index_dir=effective_embedding_index_dir,
        bm25_metadata_mode=effective_metadata_mode,
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
