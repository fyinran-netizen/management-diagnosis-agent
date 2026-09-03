from __future__ import annotations

from typing import Any


def evaluate_retrieval_quality(retrieved_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(item.get("score", 0.0)) for item in retrieved_chunks]
    embedding_scores = [
        float(item.get("embedding_score", 0.0))
        for item in retrieved_chunks
    ]
    top_score = max(scores, default=0.0)
    top_embedding_score = max(embedding_scores, default=0.0)

    chunks = []
    for item in retrieved_chunks:
        chunks.append({
            "rank": item.get("rank"),
            "retrieval_method": item.get("retrieval_method"),
            "bm25_score": item.get("bm25_score", item.get("keyword_score", 0.0)),
            "embedding_cosine_score": item.get("embedding_cosine_score", item.get("embedding_score", 0.0)),
            "normalized_bm25_score": item.get("normalized_bm25_score", item.get("normalized_keyword_score", 0.0)),
            "normalized_embedding_cosine_score": item.get("normalized_embedding_cosine_score", item.get("normalized_embedding_score", 0.0)),
            "hybrid_score": item.get("hybrid_score"),
            "rrf_score": item.get("rrf_score"),
            "keyword_rank": item.get("keyword_rank"),
            "embedding_rank": item.get("embedding_rank"),
        })

    return {
        "status": "observation",
        "chunk_count": len(retrieved_chunks),
        "top_score": top_score,
        "top_embedding_score": top_embedding_score,
        "chunks": chunks,
    }
