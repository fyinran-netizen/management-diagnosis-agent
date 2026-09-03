from __future__ import annotations

from app.tools.retrieval.retrievers.hybrid_retriever import hybrid_retrieve
from app.tools.retrieval.schemas import RetrievedChunk


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Unified retrieval interface; returned chunks include diagnostics."""
    return hybrid_retrieve(query=query, top_k=top_k)
