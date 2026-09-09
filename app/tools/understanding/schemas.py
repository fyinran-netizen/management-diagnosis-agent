from __future__ import annotations

from typing import Literal
from typing_extensions import TypedDict


UnderstandingMode = Literal["raw", "rule_based"]


class UnderstandingResult(TypedDict):
    raw_query: str
    retrieval_query: str
    mode: UnderstandingMode
    language: str
    problem_check: dict[str, object]
    problem_types: list[str]
    diagnosis_hints: list[str]
