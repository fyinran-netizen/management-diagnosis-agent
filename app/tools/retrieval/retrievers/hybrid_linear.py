from __future__ import annotations

import os

from pathlib import Path

from app.tools.retrieval.retrievers.bm25 import retrieve_by_bm25
from app.tools.retrieval.retrievers.embedding import retrieve_by_embedding
from app.tools.retrieval.fusion import linear_fusion
from app.tools.retrieval.schemas import RetrievedChunk

KEYWORD_WEIGHT = float(os.getenv("HYBRID_KEYWORD_WEIGHT", "0.15"))
EMBEDDING_WEIGHT = float(os.getenv("HYBRID_EMBEDDING_WEIGHT", "0.85"))
CANDIDATE_MULTIPLIER = int(os.getenv("HYBRID_CANDIDATE_MULTIPLIER", "5"))
MIN_CANDIDATES = int(os.getenv("HYBRID_MIN_CANDIDATES", "25"))


def hybrid_retrieve(query: str, top_k: int = 5, embedding_index_dir: Path | None = None) -> list[RetrievedChunk]:
    candidate_k = max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES)
    return linear_fusion(
        [("bm25", retrieve_by_bm25(query, candidate_k)), ("embedding", retrieve_by_embedding(query, candidate_k, index_dir=embedding_index_dir) if embedding_index_dir is not None else retrieve_by_embedding(query, candidate_k))],
        weights={"bm25": KEYWORD_WEIGHT, "embedding": EMBEDDING_WEIGHT}, top_k=top_k,
    )
