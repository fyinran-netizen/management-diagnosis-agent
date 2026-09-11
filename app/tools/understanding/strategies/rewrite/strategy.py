from __future__ import annotations

from app.core.config import GENERATION_MODEL
from app.llm.ollama_client import chat_with_ollama
from app.tools.understanding.schemas import UnderstandingResult
from app.tools.understanding.strategies.rewrite.prompts import build_rewrite_messages


def build_rewrite_understanding(
    raw_query: str,
    goal: str | None = None,
) -> UnderstandingResult:
    """Rewrite only the raw query while leaving diagnosis metadata empty."""
    del goal
    retrieval_query = chat_with_ollama(
        build_rewrite_messages(raw_query),
        model=GENERATION_MODEL,
    )
    return {
        "raw_query": raw_query,
        "retrieval_query": retrieval_query.strip(),
        "mode": "rewrite",
        "language": "",
        "problem_check": {},
        "problem_types": [],
        "diagnosis_hints": [],
    }
