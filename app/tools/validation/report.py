from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger
from app.tools.generation.schemas import DiagnosisReport


logger = get_logger("validation")


KNOWLEDGE_ITEM_CITATION_PATTERN = re.compile(
    r"(?:知识项\s*|knowledge\s+item\s*)\[?\s*(\d+)\s*\]?",
    re.IGNORECASE,
)


def extract_knowledge_item_citations(report: str) -> list[int]:
    return [int(match.group(1)) for match in KNOWLEDGE_ITEM_CITATION_PATTERN.finditer(report)]


def validate_generation_report(
    report: DiagnosisReport | dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
    section_metrics: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Apply only structural and per-section completion checks to a new report."""
    issues: list[str] = []
    failed_sections: list[str] = []
    section_names = (
        "core_diagnosis",
        "management_concepts",
        "root_causes",
        "recommendations",
    )
    metrics = section_metrics or {}

    for section_name in section_names:
        section_failed = False
        section = report.get(section_name)
        if not isinstance(section, dict):
            issues.append(f"Missing section: {section_name}.")
            failed_sections.append(section_name)
            continue

        content = section.get("content")
        if not isinstance(content, str) or not content.strip():
            issues.append(f"Section content is empty: {section_name}.")
            section_failed = True

        source_items = section.get("source_items")
        if not isinstance(source_items, list):
            issues.append(f"source_items is invalid: {section_name}.")
            section_failed = True
        elif any(
            not isinstance(item, int)
            or isinstance(item, bool)
            or not 1 <= item <= len(retrieved_chunks)
            for item in source_items
        ):
            issues.append(f"source_items contains an invalid knowledge-item number: {section_name}.")
            section_failed = True

        done_reason = metrics.get(section_name, {}).get("done_reason")
        if done_reason == "length":
            issues.append(f"Section was truncated by token length: {section_name}.")
            section_failed = True
        elif done_reason != "stop":
            issues.append(f"Section did not finish normally ({done_reason or 'missing'}): {section_name}.")
            section_failed = True

        if metrics.get(section_name, {}).get("final_parse_success") is not True:
            issues.append(f"Structured output parse failure: {section_name}.")
            section_failed = True

        if section_failed and section_name not in failed_sections:
            failed_sections.append(section_name)
        logger.debug(
            "validation section=%s passed=%s content_chars=%s source_item_count=%s done_reason=%s parse_success=%s",
            section_name,
            not section_failed,
            len(content) if isinstance(content, str) else 0,
            len(source_items) if isinstance(source_items, list) else type(source_items).__name__,
            metrics.get(section_name, {}).get("done_reason"),
            metrics.get(section_name, {}).get("final_parse_success"),
        )

    return {
        "passed": not issues,
        "issues": issues,
        "needs_revision": bool(issues),
        "failed_sections": failed_sections,
    }


def verify_report_quality(
    report: str | dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
    section_metrics: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if isinstance(report, dict):
        return validate_generation_report(report, retrieved_chunks, section_metrics)

    issues: list[str] = []

    normalized_report = report.strip().lower()

    if not normalized_report:
        issues.append("The report is empty.")

    if len(report.strip()) < 300:
        issues.append("The report is too short to be useful.")

    if retrieved_chunks:
        source_names = [item["source"] for item in retrieved_chunks]
        mentions_source = any(source in report for source in source_names)
        mentions_knowledge_basis = (
            "知识库" in report
            or "依据" in report
            or "基于" in report
            or "based on the knowledge base" in normalized_report
            or "knowledge base" in normalized_report
        )

        cited_items = extract_knowledge_item_citations(report)
        valid_citations = {item for item in cited_items if 1 <= item <= len(retrieved_chunks)}
        if not valid_citations:
            issues.append("The report does not cite retrieved knowledge items using the required format.")

        if mentions_source:
            issues.append("The report should not expose raw source file paths or source IDs.")

    has_recommendation = (
        "建议" in report
        or "行动" in report
        or "recommendation" in normalized_report
        or "action" in normalized_report
    )
    if not has_recommendation:
        issues.append("The report does not include clear practical recommendations.")

    has_assumption = (
        "假设" in report
        or "缺失信息" in report
        or "assumption" in normalized_report
        or "missing information" in normalized_report
    )
    if not has_assumption:
        issues.append("The report does not clearly separate assumptions or missing information.")

    generic_phrases = [
        "加强管理",
        "提升效率",
        "优化流程",
        "提高竞争力",
    ]
    generic_hits = [phrase for phrase in generic_phrases if phrase in report]

    if len(generic_hits) >= 2:
        issues.append("The report may contain generic management advice without enough specificity.")


    forbidden_length_notes = [
        "字数",
        "字符数",
        "token",
        "tokens",
        "word count",
        "character count",
    ]

    if any(note in normalized_report for note in forbidden_length_notes):
        issues.append("The report includes word count or length notes, which should not be included.")

    ending_punctuation = ("。", "！", "？", ".", "!", "?", "）", ")")
    if report.strip() and not report.strip().endswith(ending_punctuation):
        issues.append("The report appears to be incomplete or truncated.")

    bracket_pairs = [
        ("（", "）"),
        ("(", ")"),
        ("「", "」"),
        ("“", "”"),
        ("《", "》"),
    ]

    for left, right in bracket_pairs:
        if report.count(left) != report.count(right):
            issues.append("The report may contain unmatched brackets or quotation marks.")
            break

    passed = len(issues) == 0

    return {
        "passed": passed,
        "issues": issues,
        "needs_revision": not passed,
    }
