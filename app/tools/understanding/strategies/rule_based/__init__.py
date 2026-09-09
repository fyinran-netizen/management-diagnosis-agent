from __future__ import annotations

from app.tools.understanding.strategies.rule_based.diagnosis import build_diagnosis_hints
from app.tools.understanding.strategies.rule_based.language import detect_output_language
from app.tools.understanding.strategies.rule_based.problem_check import check_problem_clarity
from app.tools.understanding.strategies.rule_based.problem_router import route_problem
from app.tools.understanding.schemas import UnderstandingResult


def build_rule_based_understanding(
    raw_query: str,
    goal: str | None = None,
) -> UnderstandingResult:
    """Preserve the existing problem-type and diagnosis-hint query construction."""
    problem_types = route_problem(raw_query, goal)
    diagnosis_hints = build_diagnosis_hints(problem_types)
    retrieval_query = "\n".join(
        [
            raw_query,
            goal or "",
            " ".join(problem_types),
            " ".join(diagnosis_hints),
        ]
    )

    return {
        "raw_query": raw_query,
        "retrieval_query": retrieval_query,
        "mode": "rule_based",
        "language": "",
        "problem_check": {},
        "problem_types": problem_types,
    "diagnosis_hints": diagnosis_hints,
    }


__all__ = [
    "build_diagnosis_hints",
    "build_rule_based_understanding",
    "check_problem_clarity",
    "detect_output_language",
    "route_problem",
]
