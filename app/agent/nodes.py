from __future__ import annotations

from functools import wraps
from time import perf_counter
from collections.abc import Callable
from typing import Any

from app.agent.state import AgentState
from app.tools.generation import generate_report, revise_report
from app.tools.persistence.diagnosis_history import save_diagnosis_record
from app.tools.retrieval.quality import evaluate_retrieval_quality
from app.tools.retrieval.tool import retrieve_relevant_chunks
from app.tools.understanding import build_diagnosis_hints, check_problem_clarity, detect_output_language, route_problem
from app.tools.validation import verify_report_quality
from app.core.logging import get_logger

logger = get_logger("nodes")


def _logged_node(node_name: str) -> Callable[[Callable[..., dict]], Callable[..., dict]]:
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

def append_trace(state: AgentState, *, node: str, output_summary: dict, decision: str | None = None, next_node: str | None = None) -> list[dict]:
    event = {"node": node, "status": "completed", "output_summary": output_summary}
    if decision: event["decision"] = decision
    if next_node: event["next_node"] = next_node
    return state.get("trace", []) + [event]


def _summarize_issues(issues: list[object], limit: int = 5) -> str:
    summaries = [str(issue).replace("\n", " ").replace('"', "'")[:200] for issue in issues[:limit]]
    if len(issues) > limit:
        summaries.append(f"... and {len(issues) - limit} more")
    return "; ".join(summaries)

@_logged_node("understanding")
def understanding_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("understanding start")
    description = state.get("description", "").strip()
    goal = "Please identify the main management problems, analyze possible root causes, and provide practical next-step recommendations."
    language = detect_output_language(description)
    clarity = check_problem_clarity(description)
    if not clarity.get("is_clear", False):
        questions = "\n".join(f"{i}. {q}" for i, q in enumerate(clarity.get("questions", []), 1))
        logger.info("understanding fallback=clarification is_clear=false question_count=%d elapsed_seconds=%.3f", len(clarity.get("questions", [])), perf_counter() - started_at)
        logger.info("understanding completed is_clear=false elapsed_seconds=%.3f", perf_counter() - started_at)
        return {"company_context": description, "goal": goal, "language": language, "problem_check": clarity, "final_answer": f"目前信息还不足以形成可靠的管理诊断。请先补充以下信息：\n\n{questions}", "verification": {"passed": False, "issues": clarity.get("issues", []), "needs_revision": False}, "trace": append_trace(state, node="understanding", output_summary={"is_clear": False, "question_count": len(clarity.get("questions", []))}, decision="clarification")}
    problem_types = route_problem(description, goal)
    hints = build_diagnosis_hints(problem_types)
    logger.info("understanding completed is_clear=true problem_types=%s elapsed_seconds=%.3f", ",".join(problem_types), perf_counter() - started_at)
    return {"company_context": description, "goal": goal, "language": language, "problem_check": clarity, "problem_types": problem_types, "diagnosis_hints": hints, "trace": append_trace(state, node="understanding", output_summary={"is_clear": True, "problem_types": problem_types}, next_node="retrieval")}

@_logged_node("retrieval")
def retrieval_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("retrieval start strategy=linear_hybrid top_k=5")
    query = "\n".join([state.get("company_context", ""), state.get("goal", ""), " ".join(state.get("problem_types", [])), " ".join(state.get("diagnosis_hints", []))])
    chunks = retrieve_relevant_chunks(query, top_k=5)
    quality = evaluate_retrieval_quality(chunks)
    top_score = quality.get("top_score", 0.0)
    logger.info("retrieval completed strategy=linear_hybrid top_k=5 retrieved_count=%d top_score=%.4f observation=recorded elapsed_seconds=%.3f", len(chunks), top_score, perf_counter() - started_at)
    return {"retrieved_chunks": chunks, "retrieval_quality": quality, "trace": append_trace(state, node="retrieval", output_summary={"retrieved_count": len(chunks), "quality": "observation"}, next_node="generation")}

@_logged_node("generation")
def generation_node(state: AgentState) -> dict:
    started_at = perf_counter()
    from app.llm.ollama_client import get_ollama_config
    _base_url, model = get_ollama_config()
    logger.info("generation start model=%s", model)
    summary = {"problem_types": state.get("problem_types", []), "primary_problem_type": (state.get("problem_types") or ["general_management_diagnosis"])[0], "evidence_count": len(state.get("retrieved_chunks", [])), "retrieval_quality": state.get("retrieval_quality", {}).get("status", "observation")}
    report = generate_report(company_context=state["company_context"], goal=state.get("goal"), language=state.get("language", "zh"), retrieved_chunks=state.get("retrieved_chunks", []), problem_types=state.get("problem_types", []), diagnosis_hints=state.get("diagnosis_hints", []), diagnosis_summary=summary)
    logger.info("generation completed model=%s report_chars=%d elapsed_seconds=%.3f", model, len(report), perf_counter() - started_at)
    return {"report": report, "diagnosis_summary": summary, "revision_count": state.get("revision_count", 0), "trace": append_trace(state, node="generation", output_summary={"report_chars": len(report)}, next_node="validation")}

@_logged_node("validation")
def validation_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("validation start revision_count=%d", state.get("revision_count", 0))
    verification = verify_report_quality(state.get("report", ""), state.get("retrieved_chunks", []))
    count = state.get("revision_count", 0)
    next_node = "generation" if verification.get("needs_revision") and count < 1 else "persistence"
    result = {"verification": verification, "trace": append_trace(state, node="validation", output_summary={"passed": verification.get("passed", False), "issues": verification.get("issues", [])}, decision=next_node, next_node=next_node)}
    if next_node == "generation":
        logger.warning("validation retry=revision revision_count=%d issues=%d", count + 1, len(verification.get("issues", [])))
        revised = revise_report(company_context=state["company_context"], goal=state.get("goal"), language=state.get("language", "zh"), retrieved_chunks=state.get("retrieved_chunks", []), current_report=state.get("report", ""), issues=verification.get("issues", []))
        result.update({"report": revised, "revision_count": count + 1})
    issues = verification.get("issues", [])
    logger.info("validation completed passed=%s issues=%d issues=\"%s\" revision=%s elapsed_seconds=%.3f", verification.get("passed", False), len(issues), _summarize_issues(issues), next_node == "generation", perf_counter() - started_at)
    return result

@_logged_node("persistence")
def persistence_node(state: AgentState) -> dict:
    started_at = perf_counter()
    logger.info("persistence start")
    final_answer = state.get("report") or state.get("final_answer", "")
    saved_state = dict(state)
    saved_state["final_answer"] = final_answer
    project_id = save_diagnosis_record(saved_state)
    logger.info("persistence completed project_id=%s final_answer_chars=%d elapsed_seconds=%.3f", project_id, len(final_answer), perf_counter() - started_at)
    return {"project_id": project_id, "final_answer": final_answer, "trace": append_trace(state, node="persistence", output_summary={"project_id": project_id, "final_answer_chars": len(final_answer)})}
