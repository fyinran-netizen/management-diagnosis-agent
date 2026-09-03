from __future__ import annotations

import os
from typing import Any

from app.tools.retrieval.retrievers.embedding_retriever import retrieve_by_embedding
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


KEYWORD_WEIGHT = get_float_env("HYBRID_KEYWORD_WEIGHT", 0.15)
EMBEDDING_WEIGHT = get_float_env("HYBRID_EMBEDDING_WEIGHT", 0.85)
CANDIDATE_MULTIPLIER = get_int_env("HYBRID_CANDIDATE_MULTIPLIER", 5)
MIN_CANDIDATES = get_int_env("HYBRID_MIN_CANDIDATES", 25)


def result_key(item: dict[str, Any]) -> str:
    source = item.get("source", "")
    chunk_index = item.get("chunk_index")
    return f"{source}:{chunk_index}" if chunk_index is not None else source


def normalize_scores(items: list[dict[str, Any]], score_key: str, normalized_key: str) -> None:
    if not items:
        return
    max_score = max(float(item.get(score_key, 0)) for item in items)
    if max_score <= 0:
        return
    for item in items:
        item[normalized_key] = float(item.get(score_key, 0)) / max_score


def hybrid_retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    candidate_k = max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES)
    keyword_results = retrieve_by_keyword(query, top_k=candidate_k)
    embedding_results = retrieve_by_embedding(query, top_k=candidate_k)

    normalize_scores(keyword_results, "keyword_score", "normalized_keyword_score")
    normalize_scores(embedding_results, "embedding_score", "normalized_embedding_score")
    for item in keyword_results:
        item["normalized_bm25_score"] = item.get("normalized_keyword_score", 0.0)
    for item in embedding_results:
        item["normalized_embedding_cosine_score"] = item.get("normalized_embedding_score", 0.0)

    merged: dict[str, dict[str, Any]] = {}

    for item in keyword_results:
        key = result_key(item)
        merged[key] = dict(item)

    for item in embedding_results:
        key = result_key(item)
        existing = merged.get(key)
        if existing is None:
            merged[key] = dict(item)
            continue
        existing["embedding_score"] = item.get("embedding_score", 0.0)
        existing["embedding_cosine_score"] = item.get("embedding_cosine_score", item.get("embedding_score", 0.0))
        existing["normalized_embedding_score"] = item.get("normalized_embedding_score", 0.0)
        existing["normalized_embedding_cosine_score"] = item.get("normalized_embedding_cosine_score", 0.0)
        existing["retrieval_method"] = "hybrid"

    results = []
    for item in merged.values():
        keyword_score = float(item.get("normalized_keyword_score", 0.0))
        embedding_score = float(item.get("normalized_embedding_score", 0.0))
        final_score = KEYWORD_WEIGHT * keyword_score + EMBEDDING_WEIGHT * embedding_score

        item["score"] = final_score
        item["hybrid_score"] = final_score
        item.setdefault("keyword_score", 0)
        item.setdefault("bm25_score", item.get("keyword_score", 0.0))
        item.setdefault("embedding_score", 0.0)
        item.setdefault("embedding_cosine_score", item.get("embedding_score", 0.0))
        item.setdefault("normalized_keyword_score", 0.0)
        item.setdefault("normalized_embedding_score", 0.0)
        item.setdefault("normalized_bm25_score", item.get("normalized_keyword_score", 0.0))
        item.setdefault("normalized_embedding_cosine_score", item.get("normalized_embedding_score", 0.0))
        if item.get("retrieval_method") != "hybrid":
            if keyword_score > 0 and embedding_score > 0:
                item["retrieval_method"] = "hybrid"
            elif embedding_score > 0:
                item["retrieval_method"] = "embedding"
            else:
                item["retrieval_method"] = "keyword"
        results.append(item)

    results.sort(key=lambda item: item["hybrid_score"], reverse=True)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank
    return results[:top_k]


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    return hybrid_retrieve(query=query, top_k=top_k)
