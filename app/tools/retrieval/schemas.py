from __future__ import annotations

from typing import TypedDict


class RetrievedChunk(TypedDict, total=False):
    source: str
    title: str
    content: str
    score: float
    keyword_score: float
    bm25_score: float
    normalized_keyword_score: float
    normalized_bm25_score: float
    embedding_score: float
    embedding_cosine_score: float
    normalized_embedding_score: float
    normalized_embedding_cosine_score: float
    hybrid_score: float
    rrf_score: float
    keyword_rank: int
    embedding_rank: int
    rank: int
    retrieval_method: str


class RetrievalObservation(TypedDict, total=False):
    status: str
    chunk_count: int
    chunks: list[dict[str, object]]
    top_score: float
    top_embedding_score: float
