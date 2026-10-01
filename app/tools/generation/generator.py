from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.core.config import GENERATION_MODEL
from app.core.logging import get_logger
from app.llm.ollama_client import chat_with_ollama, get_last_call_metrics
from app.tools.generation.context import build_generation_context
from app.tools.generation.recovery import (
    DuplicateJSONKeyError,
    loads_rejecting_duplicate_keys,
    recover_section_json,
)
from app.tools.generation.prompts import (
    build_core_diagnosis_prompt,
    build_management_concepts_prompt,
    build_recommendations_prompt,
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


_SECTION_BUILDERS = (
    ("core_diagnosis", build_core_diagnosis_prompt),
    ("management_concepts", build_management_concepts_prompt),
    ("root_causes", build_root_causes_prompt),
    ("recommendations", build_recommendations_prompt),
)
_last_generation_section_metrics: dict[str, dict[str, Any]] = {}


def _empty_section() -> ReportSection:
    return assemble_report_section([])


def _serialized_chars(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    try:
        return len(json.dumps(value, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        return len(repr(value))


def _messages_debug_metadata(messages: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "message_count": len(messages),
        "total_chars": sum(len(message.get("content", "")) for message in messages),
        "messages": [
            {
                "role": message.get("role"),
                "content_chars": len(message.get("content", "")),
            }
            for message in messages
        ],
    }


def _context_debug_metadata(context: dict[str, Any]) -> dict[str, Any]:
    chunks = context.get("retrieved_chunks") or []
    return {
        "description_chars": len(context.get("description", "")),
        "problem_types": context.get("problem_types", []),
        "retrieved_count": len(chunks),
        "retrieved_context_chars": len(context.get("retrieved_context", "")),
        "core_diagnosis_chars": _serialized_chars(context.get("core_diagnosis"))
        if context.get("core_diagnosis") is not None else 0,
        "root_causes_chars": _serialized_chars(context.get("root_causes"))
        if context.get("root_causes") is not None else 0,
    }


def _strict_parse_failure_reason(response: Any) -> str | None:
    if isinstance(response, str):
        try:
            payload = loads_rejecting_duplicate_keys(response)
        except DuplicateJSONKeyError:
            return "duplicate_json_key"
        except (ValueError, TypeError) as exc:
            return f"invalid_json:{type(exc).__name__}"
    else:
        payload = response
    if not isinstance(payload, dict):
        return "payload_not_object"
    if set(payload) != {"sentences"}:
        return f"unexpected_keys:{sorted(payload)}"
    if _parse_sentences(payload.get("sentences")) is None:
        return "invalid_sentences"
    return None


def _parse_sentences(value: Any) -> list[ReportSentence] | None:
    if not isinstance(value, list):
        return None
    sentences: list[ReportSentence] = []
    for item in value:
        if not isinstance(item, dict):
            return None
        if set(item) != {"text", "source_items"}:
            return None
        text = item.get("text")
        source_items = item.get("source_items")
        if not isinstance(text, str) or not text.strip() or not isinstance(source_items, list):
            return None
        if not all(isinstance(source, int) and not isinstance(source, bool) for source in source_items):
            return None
        sentences.append({"text": text.strip(), "source_items": list(source_items)})
    return sentences


def _strict_parse_section(response: Any) -> tuple[ReportSection, bool]:
    """Parse only the exact structured contract; recovery is intentionally separate."""
    payload: Any = response
    if isinstance(response, str):
        try:
            payload = loads_rejecting_duplicate_keys(response)
        except (ValueError, TypeError):
            return _empty_section(), False
    if not isinstance(payload, dict):
        return _empty_section(), False
    if set(payload) != {"sentences"}:
        return _empty_section(), False

    sentences = _parse_sentences(payload.get("sentences"))
    if sentences is None:
        return _empty_section(), False
    return assemble_report_section(sentences), True


def _parse_section_response_with_status(response: Any) -> tuple[ReportSection, bool]:
    """Compatibility wrapper retained for callers importing the old helper."""
    section, success = _strict_parse_section(response)
    if success:
        return section, True
    if isinstance(response, str):
        recovered = recover_section_json(response)
        if recovered.success:
            return _strict_parse_section(recovered.value)
    return _empty_section(), False


def get_last_generation_section_metrics() -> dict[str, dict[str, Any]]:
    return {name: dict(metrics) for name, metrics in _last_generation_section_metrics.items()}


def _generate_section(
    *, section_name: str, builder: Callable[[Any], list[dict[str, str]]],
    context: dict[str, Any], call_llm: Callable[[list[dict[str, str]], str], Any],
) -> tuple[ReportSection, dict[str, Any]]:
    """Run one section through raw output, strict parse, recovery, and final parse."""
    messages = builder(context)
    logger.debug(
        "structured generation section_context_metadata section=%s metadata=%s",
        section_name,
        _context_debug_metadata(context),
    )
    logger.debug(
        "structured generation prompt_metadata section=%s metadata=%s",
        section_name,
        _messages_debug_metadata(messages),
    )
    response = call_llm(messages, GENERATION_MODEL)
    logger.debug(
        "structured generation raw_response section=%s model=%s chars=%d raw=%s",
        section_name,
        GENERATION_MODEL,
        len(response) if isinstance(response, str) else 0,
        response,
    )
    _, initial_parse_success = _strict_parse_section(response)
    if not initial_parse_success:
        logger.debug(
            "structured generation initial_parse_failure section=%s reason=%s raw_response_chars=%d",
            section_name,
            _strict_parse_failure_reason(response),
            len(response) if isinstance(response, str) else 0,
        )
    recovery_attempted = not initial_parse_success
    recovery_success = False
    recovery_method = None
    recovery_actions: list[str] = []
    final_response = response
    if recovery_attempted and isinstance(response, str):
        logger.debug(
            "structured generation recovery_input section=%s raw_response_chars=%d",
            section_name, len(response),
        )
        recovery = recover_section_json(response)
        recovery_success = recovery.success
        recovery_method = recovery.method
        recovery_actions = recovery.actions or []
        logger.debug(
            "structured generation recovery_result section=%s success=%s method=%s actions=%s repaired_payload_chars=%d",
            section_name, recovery_success, recovery_method or "none", recovery_actions,
            _serialized_chars(recovery.value) if recovery.success else 0,
        )
        if recovery.success:
            final_response = recovery.value
    section, final_parse_success = _strict_parse_section(final_response)
    logger.debug(
        "structured generation final_parse section=%s success=%s reason=%s final_payload_chars=%d content_chars=%d source_items=%d",
        section_name,
        final_parse_success,
        None if final_parse_success else _strict_parse_failure_reason(final_response),
        _serialized_chars(final_response),
        len(section["content"]),
        len(section["source_items"]),
    )
    ollama_metrics = get_last_call_metrics()
    metrics = {
        "section_name": section_name,
        "done_reason": ollama_metrics.get("done_reason"),
        "eval_count": ollama_metrics.get("eval_count"),
        "prompt_eval_count": ollama_metrics.get("prompt_eval_count"),
        "initial_parse_success": initial_parse_success,
        "final_parse_success": final_parse_success,
        # Keep the old key for downstream compatibility during migration.
        "parse_success": final_parse_success,
        "recovery_attempted": recovery_attempted,
        "recovery_success": recovery_success,
        "recovery_method": recovery_method,
        "recovery_actions": recovery_actions,
        "content_chars": len(section["content"]),
        "source_items": list(section["source_items"]),
    }
    logger.info(
        "structured generation section=%s done_reason=%s final_parse_success=%s recovery=%s content_chars=%d",
        section_name, metrics["done_reason"], final_parse_success,
        recovery_method or "none", metrics["content_chars"],
    )
    return section, metrics


def generate_diagnosis_report(*, description: str, problem_types: list[str] | None,
                              retrieved_chunks: list[dict[str, Any]] | None,
                              llm: Callable[[list[dict[str, str]], str], Any] | None = None,
                              existing_report: DiagnosisReport | None = None,
                              sections_to_generate: list[str] | None = None,
                              reset_metrics: bool = True) -> GenerationResult:
    """Generate selected sections serially, preserving unselected sections verbatim."""
    context = build_generation_context(description=description, problem_types=problem_types, retrieved_chunks=retrieved_chunks)
    call_llm = llm or (lambda messages, model: chat_with_ollama(messages, model=model))
    sections: dict[str, ReportSection] = dict(existing_report or {})
    if reset_metrics:
        _last_generation_section_metrics.clear()
    requested = set(sections_to_generate or [name for name, _ in _SECTION_BUILDERS])
    logger.debug(
        "structured generation target_sections requested=%s existing_sections=%s",
        sorted(requested), sorted(sections),
    )

    for section_name, builder in _SECTION_BUILDERS:
        if section_name not in requested:
            continue
        section_context = dict(context)
        if section_name in {"management_concepts", "root_causes", "recommendations"}:
            section_context["core_diagnosis"] = sections.get("core_diagnosis")
        if section_name == "recommendations":
            section_context["root_causes"] = sections.get("root_causes")
        section, section_metrics = _generate_section(
            section_name=section_name, builder=builder, context=section_context, call_llm=call_llm,
        )
        sections[section_name] = section
        _last_generation_section_metrics[section_name] = section_metrics

    report: DiagnosisReport = {
        "core_diagnosis": sections["core_diagnosis"],
        "management_concepts": sections["management_concepts"],
        "root_causes": sections["root_causes"],
        "recommendations": sections["recommendations"],
    }
    return {"report": report, "missing_information": []}
