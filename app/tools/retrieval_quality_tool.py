from __future__ import annotations

from typing import Any


MIN_RETRIEVED_CHUNKS = 2
MIN_TOP_SCORE = 0.12
MIN_TOP_EMBEDDING_SCORE = 0.35


def evaluate_retrieval_quality(retrieved_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not retrieved_chunks:
        return {
            "passed": False,
            "level": "none",
            "issues": ["No knowledge base chunks were retrieved."],
            "chunk_count": 0,
            "top_score": 0.0,
            "top_embedding_score": 0.0,
        }

    scores = [float(item.get("score", 0.0)) for item in retrieved_chunks]
    embedding_scores = [
        float(item.get("embedding_score", 0.0))
        for item in retrieved_chunks
    ]
    top_score = max(scores)
    top_embedding_score = max(embedding_scores)

    issues: list[str] = []
    if len(retrieved_chunks) < MIN_RETRIEVED_CHUNKS:
        issues.append("Too few knowledge base chunks were retrieved.")
    if top_score < MIN_TOP_SCORE and top_embedding_score < MIN_TOP_EMBEDDING_SCORE:
        issues.append("Top retrieval scores are too weak.")

    passed = not issues
    if passed and top_score >= 0.5:
        level = "high"
    elif passed:
        level = "medium"
    else:
        level = "low"

    return {
        "passed": passed,
        "level": level,
        "issues": issues,
        "chunk_count": len(retrieved_chunks),
        "top_score": top_score,
        "top_embedding_score": top_embedding_score,
    }
