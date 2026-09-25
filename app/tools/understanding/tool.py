from __future__ import annotations

from app.tools.understanding.schemas import (
    IntakeNormalizationResult,
    UnderstandingMode,
    UnderstandingResult,
)
from app.tools.understanding.problem_types import problem_type_label
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


def normalize_intake(
    *,
    problem_types: list[str] | None,
    description: str | None,
    other_problem_type: str | None = None,
) -> IntakeNormalizationResult:
    """Validate the production intake without expanding or rewriting it."""
    normalized_types = [item.strip() for item in (problem_types or []) if item.strip()]
    normalized_description = (description or "").strip()
    normalized_other = (other_problem_type or "").strip() or None
    errors: list[str] = []

    if not normalized_types:
        errors.append("problem_types is required")
    if not normalized_description:
        errors.append("description is required")
    if "other" in normalized_types and not normalized_other:
        errors.append("other_problem_type is required when problem_types contains 其他")

    retrieval_query = "\n".join(
        [
            f"problem_types: {', '.join(problem_type_label(item) for item in normalized_types)}",
            f"description: {normalized_description}",
            f"other_problem_type: {normalized_other or ''}",
        ]
    )
    return {
        "problem_types": normalized_types,
        "description": normalized_description,
        "other_problem_type": normalized_other,
        "intake_validation": {
            "valid": not errors,
            "errors": errors,
        },
        "retrieval_query": retrieval_query,
    }
