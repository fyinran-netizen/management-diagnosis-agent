from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from time import perf_counter

from app.agent.constants import MAX_REVISIONS
from app.agent.state import AgentState
from app.core.config import GENERATION_MODEL
from app.core.logging import get_logger
from app.llm.ollama_client import get_last_call_metrics
from app.tools.generation import (
    generate_diagnosis_report,
    get_last_generation_section_metrics,
)
from app.tools.ingestion import ingest
from app.tools.persistence.diagnosis_history import save_diagnosis_record
from app.tools.retrieval.retrieval_observation import build_retrieval_observation
from app.tools.retrieval.tool import retrieve_relevant_chunks
from app.tools.understanding import normalize_intake
from app.tools.validation import validate_generation_report


logger = get_logger("nodes")


def _error_preview(error: Exception, limit: int = 240) -> str:
    text = str(error).replace("\n", " ")
    if len(text) > limit:
        return f"{text[:limit]}... [truncated]"
    return text


def _logged_node(node_name: str) -> Callable[[Callable[..., dict]], Callable[..., dict]]:
    def decorator(function: Callable[..., dict]) -> Callable[..., dict]:
        @wraps(function)
        def wrapped(state: AgentState) -> dict:
            started_at = perf_counter()
            try:
                return function(state)
            except Exception as exc:
                logger.error(
                    "%s exception elapsed_seconds=%.3f error_type=%s error_chars=%d error=%s",
                    node_name,
                    perf_counter() - started_at,
                    type(exc).__name__,
                    len(str(exc)),
                    _error_preview(exc),
                )
                raise

        return wrapped

    return decorator


def _summarize_issues(issues: list[object], limit: int = 5) -> str:
    summaries = [
        str(issue).replace("\n", " ").replace('"', "'")[:200]
        for issue in issues[:limit]
    ]
    if len(issues) > limit:
        summaries.append(f"... and {len(issues) - limit} more")
    return "; ".join(summaries)


@_logged_node("ingestion")
def ingestion_node(state: AgentState) -> dict:
    """Reserved ingestion boundary; currently not connected in the graph."""
    del state
    result = ingest(include_private=True, include_sample=False)
    return {
        "ingestion_status": {
            "skipped": result.skipped,
            "reason": result.reason or "processed",
            "chunk_count": len(result.chunks),
        }
    }


@_logged_node("understanding")
def understanding_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("understanding start")

    intake = normalize_intake(
        problem_types=state.get("problem_types"),
        description=state.get("description"),
        other_problem_type=state.get("other_problem_type"),
    )
    logger.info(
        "understanding completed intake_valid=%s problem_types=%s elapsed_seconds=%.3f",
        intake["intake_validation"]["valid"],
        ",".join(intake["problem_types"]),
        perf_counter() - started_at,
    )
    return intake


@_logged_node("retrieval")
def retrieval_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("retrieval start strategy=hybrid_rrf top_k=5")

    chunks = retrieve_relevant_chunks(state["retrieval_query"], top_k=5)
    logger.debug(
        "retrieval chunks metadata count=%d total_content_chars=%d",
        len(chunks),
        sum(len(chunk.get("content", "")) for chunk in chunks),
    )
    quality = build_retrieval_observation(chunks)
    top_score = quality.get("top_score", 0.0)
    logger.info(
        "retrieval completed strategy=hybrid_rrf top_k=5 "
        "retrieved_count=%d top_score=%.4f observation=recorded elapsed_seconds=%.3f",
        len(chunks),
        top_score,
        perf_counter() - started_at,
    )
    return {"retrieved_chunks": chunks, "retrieval_quality": quality}


@_logged_node("generation")
def generation_node(state: AgentState) -> dict:
    started_at = perf_counter()
    revision_count = state.get("revision_count", 0)
    needs_revision = state.get("verification", {}).get("needs_revision", False)
    logger.info(
        "generation start model=%s mode=%s revision_count=%d",
        GENERATION_MODEL,
        "revision" if needs_revision else "initial",
        revision_count,
    )

    current_report = state.get("report")
    is_structured_report = (
        isinstance(current_report, dict)
        and all(isinstance(current_report.get(name), dict) for name in (
            "core_diagnosis", "management_concepts", "root_causes", "recommendations",
        ))
    )

    if needs_revision and revision_count < MAX_REVISIONS and is_structured_report:
        failed_sections = state.get("verification", {}).get("failed_sections", [])
        if not failed_sections:
            # Older verification state has no section list; preserve safety by retrying all.
            failed_sections = [
                "core_diagnosis", "management_concepts", "root_causes", "recommendations",
            ]
        logger.debug(
            "generation targeted_regeneration target_sections=%s revision_count=%d",
            failed_sections, revision_count,
        )
        generation_result = generate_diagnosis_report(
            description=state["description"],
            problem_types=state.get("problem_types", []),
            retrieved_chunks=state.get("retrieved_chunks", []),
            existing_report=current_report,
            sections_to_generate=list(failed_sections),
            reset_metrics=False,
        )
        revision_count += 1
        report = generation_result["report"]
    else:
        generation_result = generate_diagnosis_report(
            description=state["description"],
            problem_types=state.get("problem_types", []),
            retrieved_chunks=state.get("retrieved_chunks", []),
        )
        report = generation_result["report"]

    report_chars = sum(
        len(section.get("content", ""))
        for section in report.values()
        if isinstance(section, dict)
    )
    logger.info(
        "generation completed model=%s mode=%s revision_count=%d "
        "report_chars=%d elapsed_seconds=%.3f eval_count=%s "
        "prompt_eval_count=%s done_reason=%s",
        GENERATION_MODEL,
        "revision" if needs_revision else "initial",
        revision_count,
        report_chars,
        perf_counter() - started_at,
        get_last_call_metrics().get("eval_count"),
        get_last_call_metrics().get("prompt_eval_count"),
        get_last_call_metrics().get("done_reason"),
    )
    return {"report": report, "revision_count": revision_count}


@_logged_node("validation")
def validation_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("validation start revision_count=%d", state.get("revision_count", 0))
    report = state.get("report")
    report_type = type(report).__name__
    report_keys = list(report.keys()) if isinstance(report, dict) else []
    logger.debug(
        "validation report_type=%s report_keys=%s",
        report_type,
        report_keys,
    )

    verification = validate_generation_report(
        report if isinstance(report, dict) else {},
        state.get("retrieved_chunks", []),
        get_last_generation_section_metrics(),
    )
    issues = verification.get("issues", [])
    logger.info(
        "validation completed passed=%s issues=%d failed_sections=%s elapsed_seconds=%.3f",
        verification.get("passed", False),
        len(issues),
        verification.get("failed_sections", []),
        perf_counter() - started_at,
    )
    return {"verification": verification}


@_logged_node("persistence")
def persistence_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("persistence start")
    final_answer = (
        state.get("report")
        or state.get("final_answer")
        or {}
    )
    saved_state = dict(state)
    saved_state["final_answer"] = final_answer
    project_id = save_diagnosis_record(saved_state)
    logger.info(
        "persistence completed project_id=%s final_answer_chars=%d elapsed_seconds=%.3f",
        project_id,
        sum(
            len(section.get("content", ""))
            for section in final_answer.values()
            if isinstance(section, dict)
        ) if isinstance(final_answer, dict) else len(str(final_answer)),
        perf_counter() - started_at,
    )
    return {"project_id": project_id, "final_answer": final_answer}
