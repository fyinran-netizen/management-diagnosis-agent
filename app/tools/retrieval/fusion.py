from __future__ import annotations

from typing import Iterable

from app.tools.retrieval.schemas import RetrievedChunk


def result_key(item: RetrievedChunk) -> str:
    source = item.get("source", "")
    chunk_index = item.get("chunk_index")
    return f"{source}:{chunk_index}" if chunk_index is not None else source


def normalize_scores(
    items: list[RetrievedChunk], score_key: str, normalized_key: str
) -> None:
    if not items:
        return
    maximum = max(float(item.get(score_key, 0.0)) for item in items)
    if maximum <= 0:
        for item in items:
            item[normalized_key] = 0.0
        return
    for item in items:
        item[normalized_key] = float(item.get(score_key, 0.0)) / maximum


def merge_ranked_results(
    ranked_lists: Iterable[tuple[str, list[RetrievedChunk]]],
) -> dict[str, RetrievedChunk]:
    merged: dict[str, RetrievedChunk] = {}
    for method, items in ranked_lists:
        for rank, item in enumerate(items, 1):
            key = result_key(item)
            current = merged.get(key)
            if current is None:
                current = dict(item)
                merged[key] = current
            if method == "bm25":
                current["keyword_score"] = item.get("keyword_score", item.get("bm25_score", 0.0))
                current["bm25_score"] = item.get("bm25_score", item.get("keyword_score", 0.0))
                current["keyword_rank"] = rank
            elif method == "embedding":
                current["embedding_score"] = item.get("embedding_score", 0.0)
                current["embedding_cosine_score"] = item.get("embedding_cosine_score", item.get("embedding_score", 0.0))
                current["embedding_rank"] = rank
    return merged


def linear_fusion(
    ranked_lists: Iterable[tuple[str, list[RetrievedChunk]]],
    *,
    weights: dict[str, float],
    top_k: int,
) -> list[RetrievedChunk]:
    lists = list(ranked_lists)
    merged = merge_ranked_results(lists)
    for method, items in lists:
        score_key = "keyword_score" if method == "bm25" else "embedding_score"
        normalized_key = "normalized_keyword_score" if method == "bm25" else "normalized_embedding_score"
        normalize_scores(items, score_key, normalized_key)
        for item in items:
            current = merged[result_key(item)]
            current[normalized_key] = item.get(normalized_key, 0.0)
    for item in merged.values():
        value = sum(
            weights.get(method, 0.0) * float(item.get(key, 0.0))
            for method, key in (("bm25", "normalized_keyword_score"), ("embedding", "normalized_embedding_score"))
        )
        item["normalized_bm25_score"] = item.get("normalized_keyword_score", 0.0)
        item["normalized_embedding_cosine_score"] = item.get("normalized_embedding_score", 0.0)
        item["score"] = value
        item["hybrid_score"] = value
        item["retrieval_method"] = "hybrid" if item.get("keyword_rank") and item.get("embedding_rank") else ("embedding" if item.get("embedding_rank") else "keyword")
    return _rank(merged.values(), "hybrid_score", top_k)


def rrf_fusion(
    ranked_lists: Iterable[tuple[str, list[RetrievedChunk]]],
    *,
    k: float = 60.0,
    top_k: int,
) -> list[RetrievedChunk]:
    merged = merge_ranked_results(ranked_lists)
    for method, items in ranked_lists:
        for rank, item in enumerate(items, 1):
            current = merged[result_key(item)]
            current["rrf_score"] = float(current.get("rrf_score", 0.0)) + 1.0 / (k + rank)
            current.setdefault("rrf_sources", []).append(method)
    for item in merged.values():
        item["score"] = float(item.get("rrf_score", 0.0))
        item["hybrid_score"] = item["score"]
        item["retrieval_method"] = "hybrid_rrf" if len(item.get("rrf_sources", [])) > 1 else ("embedding" if item.get("embedding_rank") else "keyword")
    return _rank(merged.values(), "rrf_score", top_k)


def _rank(items: Iterable[RetrievedChunk], score_key: str, top_k: int) -> list[RetrievedChunk]:
    results = sorted(items, key=lambda item: float(item.get(score_key, 0.0)), reverse=True)[:top_k]
    for rank, item in enumerate(results, 1):
        item["rank"] = rank
    return results
