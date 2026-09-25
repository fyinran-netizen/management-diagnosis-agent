"""Data contracts for the generation boundary."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class ReportSentence(TypedDict):
    text: str
    source_items: list[int]


class ReportSection(TypedDict):
    sentences: list[ReportSentence]
    # Compatibility fields for consumers that still expect the old section shape.
    content: NotRequired[str]
    source_items: NotRequired[list[int]]


class DiagnosisReport(TypedDict):
    core_diagnosis: ReportSection
    management_concepts: ReportSection
    root_causes: ReportSection
    recommendations: ReportSection


class GenerationResult(TypedDict):
    report: DiagnosisReport
    missing_information: list[str]


class GenerationContext(TypedDict):
    description: str
    problem_types: list[str]
    retrieved_chunks: list[dict[str, Any]]
    retrieved_context: str
    core_diagnosis: ReportSection | None
    root_causes: ReportSection | None


def assemble_report_section(sentences: list[ReportSentence]) -> ReportSection:
    """Build the compatibility view from the sentence-first representation."""
    source_items: list[int] = []
    for sentence in sentences:
        for item in sentence["source_items"]:
            if item not in source_items:
                source_items.append(item)
    return {
        "sentences": sentences,
        "content": "".join(sentence["text"] for sentence in sentences),
        "source_items": source_items,
    }
