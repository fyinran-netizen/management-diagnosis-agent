from __future__ import annotations

from app.tools.understanding.schemas import UnderstandingMode, UnderstandingResult
from app.tools.understanding.strategies.raw import build_raw_understanding
from app.tools.understanding.strategies.rule_based import (
    build_rule_based_understanding,
    check_problem_clarity,
    detect_output_language,
)
from app.tools.understanding.strategies.rewrite import build_rewrite_understanding


def understand_query(
    raw_query: str,
    *,
    mode: UnderstandingMode = "rule_based",
    goal: str | None = None,
) -> UnderstandingResult:
    """Unified Understanding interface for constructing retrieval-ready queries."""
    raw_query = raw_query.strip()
    if mode == "raw":
        result = build_raw_understanding(raw_query, goal)
    elif mode == "rule_based":
        result = build_rule_based_understanding(raw_query, goal)
    elif mode == "rewrite":
        result = build_rewrite_understanding(raw_query, goal)
    else:
        raise ValueError(f"Unsupported understanding mode: {mode}")

    result["language"] = detect_output_language(raw_query)
    result["problem_check"] = check_problem_clarity(raw_query)
    return result
