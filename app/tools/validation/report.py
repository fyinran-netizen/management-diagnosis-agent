from __future__ import annotations

import re
from typing import Any


KNOWLEDGE_ITEM_CITATION_PATTERN = re.compile(
    r"(?:知识项\s*|knowledge\s+item\s*)\[?\s*(\d+)\s*\]?",
    re.IGNORECASE,
)


def extract_knowledge_item_citations(report: str) -> list[int]:
    return [int(match.group(1)) for match in KNOWLEDGE_ITEM_CITATION_PATTERN.finditer(report)]


def verify_report_quality(
    report: str,
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
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
