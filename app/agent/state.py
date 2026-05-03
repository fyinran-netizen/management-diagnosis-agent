from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    description: str
    company_context: str
    goal: str | None
    language: str

    problem_types: list[str]
    diagnosis_hints: list[str]

    retrieved_chunks: list[dict[str, Any]]
    report: str
    verification: dict[str, Any]

    revision_count: int
    project_id: str | None
    final_answer: str