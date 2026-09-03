from __future__ import annotations

import os
from typing import Any

from app.tools.retrieval.retrievers.embedding_retriever import retrieve_by_embedding
from app.tools.retrieval.retrievers.hybrid_retriever import result_key
from app.tools.retrieval.retrievers.keyword_retriever import retrieve_by_keyword


def get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


RRF_K = get_float_env("HYBRID_RRF_K", 60.0)
RRF_CANDIDATE_MULTIPLIER = get_int_env("HYBRID_RRF_CANDIDATE_MULTIPLIER", 5)
RRF_MIN_CANDIDATES = get_int_env("HYBRID_RRF_MIN_CANDIDATES", 25)


def add_rrf_scores(
    merged: dict[str, dict[str, Any]],
    items: list[dict[str, Any]],
    source_name: str,
) -> None:
    for rank, item in enumerate(items, start=1):
        key = result_key(item)
        score = 1.0 / (RRF_K + rank)
        existing = merged.get(key)
        if existing is None:
            existing = dict(item)
            existing["rrf_score"] = 0.0
            existing["rrf_sources"] = []
            merged[key] = existing
        elif source_name == "keyword":
            existing["keyword_score"] = item.get("keyword_score", 0.0)
            existing["bm25_score"] = item.get("bm25_score", item.get("keyword_score", 0.0))
        elif source_name == "embedding":
            existing["embedding_score"] = item.get("embedding_score", 0.0)
            existing["embedding_cosine_score"] = item.get("embedding_cosine_score", item.get("embedding_score", 0.0))

        existing["rrf_score"] = float(existing.get("rrf_score", 0.0)) + score
        existing["rrf_sources"] = [*existing.get("rrf_sources", []), source_name]
        existing[f"{source_name}_rank"] = rank


def hybrid_retrieve_rrf(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    candidate_k = max(top_k * RRF_CANDIDATE_MULTIPLIER, RRF_MIN_CANDIDATES)
    keyword_results = retrieve_by_keyword(query, top_k=candidate_k)
    embedding_results = retrieve_by_embedding(query, top_k=candidate_k)

    merged: dict[str, dict[str, Any]] = {}
    add_rrf_scores(merged, keyword_results, "keyword")
    add_rrf_scores(merged, embedding_results, "embedding")

    results = []
    for item in merged.values():
        rrf_score = float(item.get("rrf_score", 0.0))
        item["score"] = rrf_score
        item["hybrid_score"] = rrf_score
        item.setdefault("keyword_score", 0)
        item.setdefault("bm25_score", item.get("keyword_score", 0.0))
        item.setdefault("embedding_score", 0.0)
        item.setdefault("embedding_cosine_score", item.get("embedding_score", 0.0))

        sources = set(item.get("rrf_sources", []))
        if {"keyword", "embedding"}.issubset(sources):
            item["retrieval_method"] = "hybrid_rrf"
        elif "embedding" in sources:
            item["retrieval_method"] = "embedding"
        else:
            item["retrieval_method"] = "keyword"

        results.append(item)

    results.sort(key=lambda item: item["rrf_score"], reverse=True)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank
    return results[:top_k]
