from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

from app.core.config import HF_CACHE_DIR, RERANKER_MODEL, TORCH_CACHE_DIR
from app.tools.retrieval.schemas import RetrievedChunk
from app.tools.retrieval.retrievers.embedding import chunk_to_embedding_text

os.environ.setdefault("HF_HOME", str(HF_CACHE_DIR))
os.environ.setdefault("TORCH_HOME", str(TORCH_CACHE_DIR))

from sentence_transformers import CrossEncoder


def get_reranker_model_name() -> str:
    return RERANKER_MODEL


def get_reranker_cache_dir() -> str:
    return str(HF_CACHE_DIR.resolve())


def should_use_local_files_only() -> bool:
    value = os.getenv("RERANKER_LOCAL_FILES_ONLY", "true").lower().strip()
    return value in {"true", "1", "yes", "y"}


@lru_cache(maxsize=1)
def get_reranker_model() -> CrossEncoder:
    return CrossEncoder(
        get_reranker_model_name(),
        cache_folder=get_reranker_cache_dir(),
        local_files_only=should_use_local_files_only(),
    )


def score_candidates(
    query: str,
    candidates: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    """Add BGE rerank scores to candidates without changing pipeline order."""
    if not candidates:
        return []

    pairs = [(query, _candidate_text(candidate)) for candidate in candidates]
    scores = np.asarray(get_reranker_model().predict(pairs), dtype=float).reshape(-1)
    if len(scores) != len(candidates):
        raise ValueError("Reranker returned a score count different from candidates")

    scored = []
    for candidate, score in zip(candidates, scores, strict=True):
        item = dict(candidate)
        item["rerank_score"] = float(score)
        scored.append(item)

    return scored


def rerank(
    query: str,
    candidates: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    """Compatibility wrapper for callers still using the old method name.

    Scoring only is intentional; sorting and Top-K selection belong to the
    surrounding retrieval pipeline.
    """
    return score_candidates(query, candidates)


def _candidate_text(candidate: RetrievedChunk) -> str:
    return chunk_to_embedding_text(candidate)