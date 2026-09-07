from __future__ import annotations

import os

from app.tools.retrieval.retrievers.bm25 import retrieve_by_bm25
from app.tools.retrieval.retrievers.embedding import retrieve_by_embedding
from app.tools.retrieval.fusion import rrf_fusion
from app.tools.retrieval.schemas import RetrievedChunk

RRF_K = float(os.getenv("HYBRID_RRF_K", "60.0"))
RRF_CANDIDATE_MULTIPLIER = int(os.getenv("HYBRID_RRF_CANDIDATE_MULTIPLIER", "5"))
RRF_MIN_CANDIDATES = int(os.getenv("HYBRID_RRF_MIN_CANDIDATES", "25"))


def hybrid_retrieve_rrf(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    candidate_k = max(top_k * RRF_CANDIDATE_MULTIPLIER, RRF_MIN_CANDIDATES)
    return rrf_fusion(
        [("bm25", retrieve_by_bm25(query, candidate_k)), ("embedding", retrieve_by_embedding(query, candidate_k))],
        k=RRF_K, top_k=top_k,
    )
