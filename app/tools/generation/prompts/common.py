"""Shared prompt plumbing for section generation."""

from __future__ import annotations

import json
from typing import Any

from app.tools.generation.schemas import GenerationContext


COMMON_RULES = """
You are generating one section of a management diagnosis report.

Output Chinese by default; professional management terms may remain in English.
Use only the user description, problem_types, and retrieved knowledge. Do not invent
company facts that the user did not provide. Treat retrieved knowledge as management
concepts, mechanisms, or practices to be absorbed into the analysis, not as text to
be listed or quoted as an internal source.

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
    """Build the shared JSON-output envelope for section generation."""
    user_context: dict[str, Any] = {
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
