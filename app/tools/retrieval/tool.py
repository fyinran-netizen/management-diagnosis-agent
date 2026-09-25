from __future__ import annotations

from app.core.config import (
    PRODUCTION_RETRIEVAL_BM25_METADATA_MODE,
    PRODUCTION_RETRIEVAL_CANDIDATE_K,
    PRODUCTION_RETRIEVAL_CORPUS_DIR,
    PRODUCTION_RETRIEVAL_EMBEDDING_INDEX_DIR,
)
from app.tools.retrieval.pipeline import retrieve_pipeline
from app.tools.retrieval.schemas import RetrievedChunk


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Unified retrieval interface; returned chunks include diagnostics."""
    return retrieve_pipeline(
        query=query,
        mode="hybrid",
        final_k=top_k,
        source_retrieval_k=PRODUCTION_RETRIEVAL_CANDIDATE_K,
        corpus_dir=PRODUCTION_RETRIEVAL_CORPUS_DIR,
        embedding_index_dir=PRODUCTION_RETRIEVAL_EMBEDDING_INDEX_DIR,
        bm25_metadata_mode=PRODUCTION_RETRIEVAL_BM25_METADATA_MODE,
    )
