"""Resolve model-returned knowledge-item numbers to safe source metadata."""

from __future__ import annotations

from typing import Any, TypedDict

from app.tools.generation.schemas import DiagnosisReport


class SourceReference(TypedDict):
    chapter_number: str
    section_number: str
    summary: str


def _summary_for_chunk(chunk: dict[str, Any]) -> str:
    summary = chunk.get("summary")
    return summary.strip() if isinstance(summary, str) and summary.strip() else ""


def resolve_source_items(
    source_items: list[int], retrieved_chunks: list[dict[str, Any]]
) -> list[SourceReference]:
    """Map 1-based item numbers and deduplicate public sources by chapter/section."""
    resolved: list[SourceReference] = []
    seen: set[tuple[str, str]] = set()
    resolved_by_key: dict[tuple[str, str], SourceReference] = {}
    for item_number in source_items:
        if not 1 <= item_number <= len(retrieved_chunks):
            continue
        chunk = retrieved_chunks[item_number - 1]
        key = (str(chunk.get("chapter_title", "")), str(chunk.get("section_title", "")))
        summary = _summary_for_chunk(chunk)
        if key in seen:
            existing = resolved_by_key[key]
            if not existing["summary"] and summary:
                existing["summary"] = summary
            continue
        seen.add(key)
        source = {
                "chapter_number": str(chunk.get("chapter_number", "-")),
                "section_number": str(chunk.get("section_number", "-")),
            "summary": summary,
        }
        resolved.append(source)
        resolved_by_key[key] = source
    return resolved


def resolve_report_sources(
    report: DiagnosisReport, retrieved_chunks: list[dict[str, Any]]
) -> dict[str, list[SourceReference]]:
    """Resolve every section's item numbers while retaining chunks internally."""
    return {
        section_name: resolve_source_items(section["source_items"], retrieved_chunks)
        for section_name, section in report.items()
    }
