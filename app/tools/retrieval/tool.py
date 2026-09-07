from __future__ import annotations

from app.tools.retrieval.pipeline import retrieve_pipeline
from app.tools.retrieval.schemas import RetrievedChunk


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Unified retrieval interface; returned chunks include diagnostics."""
    return retrieve_pipeline(query=query, final_top_k=top_k)
