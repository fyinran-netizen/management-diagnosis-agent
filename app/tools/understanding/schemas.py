from __future__ import annotations

from typing import Literal
from typing_extensions import TypedDict


UnderstandingMode = Literal["raw", "rule_based", "rewrite"]


class UnderstandingResult(TypedDict):
    raw_query: str
    retrieval_query: str
    mode: UnderstandingMode
    language: str
    problem_check: dict[str, object]
    problem_types: list[str]
    diagnosis_hints: list[str]


class IntakeNormalizationResult(TypedDict):
    problem_types: list[str]
    description: str
    other_problem_type: str | None
    intake_validation: dict[str, object]
    retrieval_query: str
