from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any

from app.agent.constants import MAX_REVISIONS
from app.agent.state import AgentState
from app.core.config import GENERATION_MODEL
from app.core.logging import get_logger
from app.tools.generation import generate_report, revise_report
from app.tools.persistence.diagnosis_history import save_diagnosis_record
from app.tools.retrieval.retrieval_observation import build_retrieval_observation
from app.tools.retrieval.tool import retrieve_relevant_chunks
from app.tools.understanding import (
    build_diagnosis_hints,
    check_problem_clarity,
    detect_output_language,
    route_problem,
)
from app.tools.validation import verify_report_quality


logger = get_logger("nodes")


def _logged_node(
    node_name: str,
) -> Callable[[Callable[..., dict]], Callable[..., dict]]:
    def decorator(function: Callable[..., dict]) -> Callable[..., dict]:
        @wraps(function)
        def wrapped(state: AgentState) -> dict:
            started_at = perf_counter()
            try:
                return function(state)
            except Exception as exc:
                logger.error(
                    "%s exception elapsed_seconds=%.3f error=%s",
                    node_name,
                    perf_counter() - started_at,
                    str(exc).replace("\n", " ")[:500],
                )
                raise

        return wrapped

    return decorator


def _summarize_issues(
    issues: list[object],
    limit: int = 5,
) -> str:
    summaries = [
        str(issue).replace("\n", " ").replace('"', "'")[:200]
        for issue in issues[:limit]
    ]

    if len(issues) > limit:
        summaries.append(f"... and {len(issues) - limit} more")

    return "; ".join(summaries)


@_logged_node("understanding")
def understanding_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("understanding start")

    description = state.get("description", "").strip()
    goal = (
        "Please identify the main management problems, analyze possible root causes, "
        "and provide practical next-step recommendations."
    )

    language = detect_output_language(description)
    clarity = check_problem_clarity(description)

    if not clarity.get("is_clear", False):
        questions = "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(
                clarity.get("questions", []),
                start=1,
            )
        )

        logger.info(
            "understanding completed is_clear=false question_count=%d elapsed_seconds=%.3f",
            len(clarity.get("questions", [])),
            perf_counter() - started_at,
        )

        return {
            "company_context": description,
            "goal": goal,
            "language": language,
            "problem_check": clarity,
            "final_answer": (
                "目前信息还不足以形成可靠的管理诊断。"
                f"请先补充以下信息：\n\n{questions}"
            ),
            "verification": {
                "passed": False,
                "issues": clarity.get("issues", []),
                "needs_revision": False,
            },
        }

    problem_types = route_problem(description, goal)
    hints = build_diagnosis_hints(problem_types)

    logger.info(
        "understanding completed is_clear=true problem_types=%s elapsed_seconds=%.3f",
        ",".join(problem_types),
        perf_counter() - started_at,
    )

    return {
        "company_context": description,
        "goal": goal,
        "language": language,
        "problem_check": clarity,
        "problem_types": problem_types,
        "diagnosis_hints": hints,
    }


@_logged_node("retrieval")
def retrieval_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("retrieval start strategy=linear_hybrid top_k=5")

    query = "\n".join(
        [
            state.get("company_context", ""),
            state.get("goal", ""),
            " ".join(state.get("problem_types", [])),
            " ".join(state.get("diagnosis_hints", [])),
        ]
    )

    chunks = retrieve_relevant_chunks(query, top_k=5)
    quality = build_retrieval_observation(chunks)
    top_score = quality.get("top_score", 0.0)

    logger.info(
        "retrieval completed strategy=linear_hybrid top_k=5 "
        "retrieved_count=%d top_score=%.4f observation=recorded elapsed_seconds=%.3f",
        len(chunks),
        top_score,
        perf_counter() - started_at,
    )

    return {
        "retrieved_chunks": chunks,
        "retrieval_quality": quality,
    }


@_logged_node("generation")
def generation_node(state: AgentState) -> dict:
    started_at = perf_counter()

    revision_count = state.get("revision_count", 0)
    needs_revision = state.get("verification", {}).get(
        "needs_revision",
        False,
    )

    logger.info(
        "generation start model=%s mode=%s revision_count=%d",
        GENERATION_MODEL,
        "revision" if needs_revision else "initial",
        revision_count,
    )

    if needs_revision and revision_count < MAX_REVISIONS:
        report = revise_report(
            company_context=state["company_context"],
            goal=state.get("goal"),
            language=state.get("language", "zh"),
            retrieved_chunks=state.get("retrieved_chunks", []),
            current_report=state.get("report", ""),
            issues=state.get("verification", {}).get("issues", []),
        )

        revision_count += 1
        diagnosis_summary = state.get("diagnosis_summary", {})

    else:
        diagnosis_summary = {
            "problem_types": state.get("problem_types", []),
            "primary_problem_type": (
                state.get("problem_types")
                or ["general_management_diagnosis"]
            )[0],
            "evidence_count": len(
                state.get("retrieved_chunks", [])
            ),
            "retrieval_quality": state.get(
                "retrieval_quality",
                {},
            ).get("status", "observation"),
        }

        report = generate_report(
            company_context=state["company_context"],
            goal=state.get("goal"),
            language=state.get("language", "zh"),
            retrieved_chunks=state.get("retrieved_chunks", []),
            problem_types=state.get("problem_types", []),
            diagnosis_hints=state.get("diagnosis_hints", []),
            diagnosis_summary=diagnosis_summary,
        )

    logger.info(
        "generation completed model=%s report_chars=%d elapsed_seconds=%.3f",
        GENERATION_MODEL,
        len(report),
        perf_counter() - started_at,
    )

    return {
        "report": report,
        "diagnosis_summary": diagnosis_summary,
        "revision_count": revision_count,
    }


@_logged_node("validation")
def validation_node(state: AgentState) -> dict:
    started_at = perf_counter()

    logger.info(
        "validation start revision_count=%d",
        state.get("revision_count", 0),
    )

    verification = verify_report_quality(
        state.get("report", ""),
        state.get("retrieved_chunks", []),
    )

    issues = verification.get("issues", [])

    logger.info(
        'validation completed passed=%s issues=%d issues="%s" elapsed_seconds=%.3f',
        verification.get("passed", False),
        len(issues),
        _summarize_issues(issues),
        perf_counter() - started_at,
    )

    return {
        "verification": verification,
    }


@_logged_node("persistence")
def persistence_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("persistence start")

    final_answer = (
        state.get("report")
        or state.get("final_answer", "")
    )

    saved_state = dict(state)
    saved_state["final_answer"] = final_answer

    project_id = save_diagnosis_record(saved_state)

    logger.info(
        "persistence completed project_id=%s final_answer_chars=%d elapsed_seconds=%.3f",
        project_id,
        len(final_answer),
        perf_counter() - started_at,
    )

    return {
        "project_id": project_id,
        "final_answer": final_answer,
    }
