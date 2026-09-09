from __future__ import annotations

from app.tools.understanding.schemas import UnderstandingResult


def build_raw_understanding(raw_query: str, goal: str | None = None) -> UnderstandingResult:
    """Use the user's input directly as the retrieval query."""
    del goal
    return {
        "raw_query": raw_query,
        "retrieval_query": raw_query,
        "mode": "raw",
        "language": "",
        "problem_check": {},
        "problem_types": [],
        "diagnosis_hints": [],
    }
