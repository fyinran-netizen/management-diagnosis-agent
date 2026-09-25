from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.core.config import GENERATION_MODEL
from app.core.logging import get_logger
from app.llm.ollama_client import chat_with_ollama, get_last_call_metrics
from app.tools.generation.context import build_generation_context
from app.tools.generation.prompts import (
    build_core_diagnosis_prompt,
    build_generation_messages,
    build_management_concepts_prompt,
    build_recommendations_prompt,
    build_revision_messages,
    build_root_causes_prompt,
)
from app.tools.generation.schemas import (
    DiagnosisReport,
    GenerationResult,
    ReportSection,
    ReportSentence,
    assemble_report_section,
)


logger = get_logger("generation")


def generate_report(*, company_context: str, goal: str | None, language: str,
                    retrieved_chunks: list[dict[str, Any]], problem_types: list[str],
                    diagnosis_hints: list[str], diagnosis_summary: dict[str, Any]) -> str:
    messages = build_generation_messages(company_context, goal, language, retrieved_chunks, problem_types, diagnosis_hints, diagnosis_summary)
    return chat_with_ollama(messages, model=GENERATION_MODEL)


def revise_report(*, company_context: str, goal: str | None, language: str,
                  retrieved_chunks: list[dict[str, Any]], current_report: str,
                  issues: list[str]) -> str:
    messages = build_revision_messages(company_context, goal, language, retrieved_chunks, current_report, issues)
    return chat_with_ollama(messages, model=GENERATION_MODEL)


_SECTION_BUILDERS = (
    ("core_diagnosis", build_core_diagnosis_prompt),
    ("management_concepts", build_management_concepts_prompt),
    ("root_causes", build_root_causes_prompt),
    ("recommendations", build_recommendations_prompt),
)
_last_generation_section_metrics: dict[str, dict[str, Any]] = {}


def _empty_section() -> ReportSection:
    return assemble_report_section([])


def _parse_sentences(value: Any) -> list[ReportSentence] | None:
    if not isinstance(value, list):
        return None
    sentences: list[ReportSentence] = []
    for item in value:
        if not isinstance(item, dict):
            return None
        text = item.get("text")
        source_items = item.get("source_items")
        if not isinstance(text, str) or not text.strip() or not isinstance(source_items, list):
            return None
        if not all(isinstance(source, int) and not isinstance(source, bool) for source in source_items):
            return None
        sentences.append({"text": text.strip(), "source_items": list(source_items)})
    return sentences


def _parse_section_response_with_status(response: Any) -> tuple[ReportSection, bool]:
    """Parse the sentence-first structured section and derive compatibility fields."""
    payload: Any = response
    if isinstance(response, str):
        try:
            payload = json.loads(response)
        except (ValueError, TypeError):
            return _empty_section(), False
    if not isinstance(payload, dict):
        return _empty_section(), False
    if any(key in payload for key in ("content", "source_items", "statements")):
        return _empty_section(), False

    sentences = _parse_sentences(payload.get("sentences"))
    if sentences is None:
        return _empty_section(), False
    return assemble_report_section(sentences), True


def get_last_generation_section_metrics() -> dict[str, dict[str, Any]]:
    return {name: dict(metrics) for name, metrics in _last_generation_section_metrics.items()}


def generate_diagnosis_report(*, description: str, problem_types: list[str] | None,
                              retrieved_chunks: list[dict[str, Any]] | None,
                              llm: Callable[[list[dict[str, str]], str], Any] | None = None) -> GenerationResult:
    """Generate the four sections serially, passing only required prior sections."""
    context = build_generation_context(description=description, problem_types=problem_types, retrieved_chunks=retrieved_chunks)
    call_llm = llm or (lambda messages, model: chat_with_ollama(messages, model=model))
    sections: dict[str, ReportSection] = {}
    _last_generation_section_metrics.clear()

    for section_name, builder in _SECTION_BUILDERS:
        section_context = dict(context)
        if section_name in {"management_concepts", "root_causes", "recommendations"}:
            section_context["core_diagnosis"] = sections.get("core_diagnosis")
        if section_name == "recommendations":
            section_context["root_causes"] = sections.get("root_causes")
        response = call_llm(builder(section_context), GENERATION_MODEL)
        section, parse_success = _parse_section_response_with_status(response)
        sections[section_name] = section
        ollama_metrics = get_last_call_metrics()
        section_metrics = {
            "section_name": section_name,
            "done_reason": ollama_metrics.get("done_reason"),
            "eval_count": ollama_metrics.get("eval_count"),
            "prompt_eval_count": ollama_metrics.get("prompt_eval_count"),
            "parse_success": parse_success,
            "content_chars": len(section["content"]),
            "source_items": list(section["source_items"]),
        }
        _last_generation_section_metrics[section_name] = section_metrics
        logger.info(
            "structured generation section=%s done_reason=%s eval_count=%s prompt_eval_count=%s parse_success=%s content_chars=%d source_items=%s",
            section_name,
            section_metrics["done_reason"],
            section_metrics["eval_count"],
            section_metrics["prompt_eval_count"],
            parse_success,
            section_metrics["content_chars"],
            section_metrics["source_items"],
        )

    report: DiagnosisReport = {
        "core_diagnosis": sections["core_diagnosis"],
        "management_concepts": sections["management_concepts"],
        "root_causes": sections["root_causes"],
        "recommendations": sections["recommendations"],
    }
    return {"report": report, "missing_information": []}
