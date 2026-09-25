from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict

from app.tools.generation.schemas import DiagnosisReport


class AgentState(TypedDict, total=False):
    problem_types: list[str]
    description: str
    other_problem_type: str | None
    intake_validation: dict[str, Any]
    retrieval_query: str

    retrieved_chunks: list[dict[str, Any]]
    retrieval_quality: dict[str, Any]
    report: DiagnosisReport
    verification: dict[str, Any]
    revision_count: int
    project_id: str | None
    final_answer: DiagnosisReport
    trace: list[dict[str, Any]]
