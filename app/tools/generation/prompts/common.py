"""Shared prompt plumbing for section generation."""

from __future__ import annotations

import json
from typing import Any

from app.tools.generation.context import format_retrieved_context
from app.tools.generation.schemas import GenerationContext


def format_diagnosis_hints(diagnosis_hints: list[str] | None) -> str:
    return "\n".join(f"- {hint}" for hint in (diagnosis_hints or [])) or "无特定诊断提示。"


COMMON_RULES = """
You are generating one section of a management diagnosis report.

Output Chinese by default; professional management terms may remain in English.
Use only the user description, problem_types, and retrieved knowledge. Do not invent
company facts that the user did not provide. Treat retrieved knowledge as management
concepts, mechanisms, or practices to be absorbed into the analysis, not as text to
be listed or quoted as an internal source.

The labels “知识项1”“知识项2” and similar labels that may appear in the retrieved
context are metadata for source_items only. Never copy, paraphrase, or refer to those
labels in text. Do not write “知识项N”“根据知识项N”“依据知识项N” or wording that
describes the source instead of explaining the management point.

Before returning the JSON, scan every text value and remove any occurrence of “知识项”
and any phrase such as “根据……指出”“依据……显示”“检索内容表明” or “来源说明”. Replace
it with the actual management explanation, or omit the claim if it cannot be stated
without referring to a source. The text values must read as ordinary report prose.

When making an inference, use uncertainty language such as “可能”“更可能”或“如果属实”.
Do not expose filenames, file paths, source IDs, chunk IDs, raw metadata, or internal
retrieval references in report text. Do not use “知识项N”“根据知识项N”“依据知识项N”
or equivalent source-description wording. Source attribution belongs only in source_items.

Return exactly one JSON object with this shape:
{"sentences":[{"text":"...", "source_items":[1,3]}]}

Each text field contains report content only. source_items contains the 1-based retrieved-
knowledge numbers actually used for that text; it may contain multiple numbers. Return no
extra fields or explanatory text. Do not output chain-of-thought, hidden reasoning, word
counts, or token counts.
""".strip()


def build_section_messages(
    context: GenerationContext,
    section_name: str,
    section_instructions: str,
) -> list[dict[str, str]]:
    """Build the shared JSON-output envelope for a section prompt."""
    user_context = {
        "section": section_name,
        "description": context["description"],
        "problem_types": context["problem_types"],
        "retrieved_knowledge": context["retrieved_context"],
    }
    if context.get("core_diagnosis") is not None:
        user_context["core_diagnosis"] = context["core_diagnosis"]
    if context.get("root_causes") is not None:
        user_context["root_causes"] = context["root_causes"]

    return [
        {"role": "system", "content": f"{COMMON_RULES}\n\n{section_instructions}"},
        {"role": "user", "content": json.dumps(user_context, ensure_ascii=False, default=str)},
    ]


def build_generation_messages(
    company_context: str,
    goal: str | None,
    language: str,
    retrieved_chunks: list[dict[str, Any]],
    problem_types: list[str] | None = None,
    diagnosis_hints: list[str] | None = None,
    diagnosis_summary: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Compatibility envelope for the pre-refactor single-report caller."""
    del language, problem_types, diagnosis_hints, diagnosis_summary
    context = {
        "description": company_context,
        "problem_types": [],
        "retrieved_chunks": retrieved_chunks,
        "retrieved_context": format_retrieved_context(retrieved_chunks),
    }
    messages = build_section_messages(
        context,
        "legacy_report",
        "Return the legacy report response without exposing internal source metadata.",
    )
    messages[1]["content"] += f"\ngoal={goal or '未指定'}"
    return messages


def build_revision_messages(
    company_context: str,
    goal: str | None,
    language: str,
    retrieved_chunks: list[dict[str, Any]],
    current_report: str,
    issues: list[str],
) -> list[dict[str, str]]:
    """Compatibility envelope for the existing validation revision loop."""
    del language
    messages = build_generation_messages(company_context, goal, "zh", retrieved_chunks)
    messages[0]["content"] = "TODO: revision instructions."
    messages[1]["content"] += f"\ncurrent_report={current_report}\nissues={issues}"
    return messages
