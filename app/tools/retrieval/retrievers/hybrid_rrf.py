from __future__ import annotations

import os
from pathlib import Path

from app.tools.retrieval.retrievers.bm25 import retrieve_by_bm25
from app.tools.retrieval.retrievers.embedding import retrieve_by_embedding
from app.tools.retrieval.fusion import rrf_fusion
from app.tools.retrieval.schemas import RetrievedChunk

RRF_K = float(os.getenv("HYBRID_RRF_K", "60.0"))
RRF_CANDIDATE_MULTIPLIER = int(os.getenv("HYBRID_RRF_CANDIDATE_MULTIPLIER", "5"))
RRF_MIN_CANDIDATES = int(os.getenv("HYBRID_RRF_MIN_CANDIDATES", "25"))


def hybrid_retrieve_rrf(
    query: str,
    top_k: int = 5,
    embedding_index_dir: Path | None = None,
    *,
    corpus_dir: Path | None = None,
    bm25_metadata_mode: str | None = None,
) -> list[RetrievedChunk]:
    candidate_k = max(top_k * RRF_CANDIDATE_MULTIPLIER, RRF_MIN_CANDIDATES)
    bm25_kwargs = {}
    if corpus_dir is not None:
        bm25_kwargs["corpus_dir"] = corpus_dir
    if bm25_metadata_mode is not None:
        bm25_kwargs["metadata_mode"] = bm25_metadata_mode
    return rrf_fusion(
        [("bm25", retrieve_by_bm25(query, candidate_k, **bm25_kwargs)), ("embedding", retrieve_by_embedding(query, candidate_k, index_dir=embedding_index_dir) if embedding_index_dir is not None else retrieve_by_embedding(query, candidate_k))],
        k=RRF_K, top_k=top_k,
    )
