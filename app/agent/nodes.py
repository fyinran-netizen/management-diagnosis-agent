from __future__ import annotations

from app.agent.prompts import build_generation_messages, build_revision_messages
from app.agent.state import AgentState
from app.llm.ollama_client import chat_with_ollama
from app.memory.project_memory import save_project_record
from app.rag.retriever import retrieve_relevant_chunks
from app.tools.diagnosis_tools import build_diagnosis_hints
from app.tools.problem_check_tool import check_problem_clarity
from app.tools.problem_router_tool import route_problem
from app.tools.retrieval_quality_tool import evaluate_retrieval_quality
from app.tools.verify_tool import verify_report_quality
from app.tools.language_tool import detect_output_language


def append_trace(
    state: AgentState,
    *,
    node: str,
    output_summary: dict,
    decision: str | None = None,
    next_node: str | None = None,
) -> list[dict]:
    event = {
        "node": node,
        "status": "completed",
        "output_summary": output_summary,
    }
    if decision:
        event["decision"] = decision
    if next_node:
        event["next_node"] = next_node
    return state.get("trace", []) + [event]


def intake_node(state: AgentState) -> dict:
    """
    Convert the user's raw description into internal fields used by later nodes.

    The user only needs to provide one free-form description.
    This node prepares:
    - company_context
    - goal
    - language
    """
    description = state.get("description", "").strip()

    default_goal = (
        "Please identify the main management problems, analyze possible root causes, "
        "and provide practical next-step recommendations."
    )

    return {
        "company_context": description,
        "goal": default_goal,
        "language": detect_output_language(description),
        "trace": append_trace(
            state,
            node="intake",
            output_summary={
                "language": detect_output_language(description),
                "description_chars": len(description),
            },
            next_node="problem_check",
        ),
    }


def problem_check_node(state: AgentState) -> dict:
    """
    Decide whether the input is specific enough for a useful diagnosis.
    """
    problem_check = check_problem_clarity(state.get("company_context", ""))
    next_node = "route" if problem_check.get("is_clear", False) else "clarification"
    return {
        "problem_check": problem_check,
        "trace": append_trace(
            state,
            node="problem_check",
            output_summary={
                "is_clear": problem_check.get("is_clear", False),
                "issues": problem_check.get("issues", []),
                "signal_terms": problem_check.get("signal_terms", []),
            },
            decision=next_node,
            next_node=next_node,
        ),
    }


def clarification_node(state: AgentState) -> dict:
    """
    Return clarification questions instead of forcing a weak diagnosis.
    """
    problem_check = state.get("problem_check", {})
    questions = problem_check.get("questions", [])
    question_lines = "\n".join([f"{index}. {question}" for index, question in enumerate(questions, start=1)])
    final_answer = (
        "目前信息还不足以形成可靠的管理诊断。请先补充以下信息：\n\n"
        f"{question_lines}"
    )

    return {
        "final_answer": final_answer,
        "verification": {
            "passed": False,
            "issues": problem_check.get("issues", []),
            "needs_revision": False,
        },
        "trace": append_trace(
            state,
            node="clarification",
            output_summary={
                "question_count": len(questions),
            },
        ),
    }


def route_node(state: AgentState) -> dict:
    """
    Classify the raw management problem into problem types.

    Example:
    - customer_value_misalignment
    - metrics_misalignment
    - opportunity_neglect
    - control_over_self_drive
    """
    problem_types = route_problem(
        company_context=state.get("company_context", ""),
        goal=state.get("goal"),
    )

    diagnosis_hints = build_diagnosis_hints(problem_types)

    return {
        "problem_types": problem_types,
        "diagnosis_hints": diagnosis_hints,
        "trace": append_trace(
            state,
            node="route",
            output_summary={
                "problem_types": problem_types,
                "hint_count": len(diagnosis_hints),
            },
            next_node="retrieve",
        ),
    }


def retrieve_node(state: AgentState) -> dict:
    """
    Retrieve relevant knowledge chunks from the local knowledge base.
    """
    query = (
        f"{state.get('company_context', '')}\n"
        f"{state.get('goal', '')}\n"
        f"{' '.join(state.get('problem_types', []))}\n"
        f"{' '.join(state.get('diagnosis_hints', []))}"
    )

    retrieved_chunks = retrieve_relevant_chunks(
        query=query,
        top_k=5,
    )

    return {
        "retrieved_chunks": retrieved_chunks,
        "trace": append_trace(
            state,
            node="retrieve",
            output_summary={
                "retrieved_count": len(retrieved_chunks),
                "top_sources": [
                    item.get("source")
                    for item in retrieved_chunks[:3]
                ],
            },
            next_node="retrieval_check",
        ),
    }


def retrieval_check_node(state: AgentState) -> dict:
    """
    Check whether retrieved evidence is strong enough for a grounded report.
    """
    retrieval_quality = evaluate_retrieval_quality(state.get("retrieved_chunks", []))
    next_node = "diagnose" if retrieval_quality.get("passed", False) else "low_confidence"
    return {
        "retrieval_quality": retrieval_quality,
        "trace": append_trace(
            state,
            node="retrieval_check",
            output_summary={
                "passed": retrieval_quality.get("passed", False),
                "level": retrieval_quality.get("level", "unknown"),
                "chunk_count": retrieval_quality.get("chunk_count", 0),
                "top_score": retrieval_quality.get("top_score", 0.0),
                "top_embedding_score": retrieval_quality.get("top_embedding_score", 0.0),
                "issues": retrieval_quality.get("issues", []),
            },
            decision=next_node,
            next_node=next_node,
        ),
    }


def low_confidence_node(state: AgentState) -> dict:
    """
    Stop before generation when retrieval evidence is too weak.
    """
    retrieval_quality = state.get("retrieval_quality", {})
    issues = retrieval_quality.get("issues", [])
    issue_lines = "\n".join([f"- {issue}" for issue in issues]) or "- 检索结果不足。"
    final_answer = (
        "当前知识库匹配度较弱，我不建议直接生成完整诊断报告。\n\n"
        "需要补充的信息：\n"
        "- 具体业务症状，例如增长、客户、利润、效率或组织协同的变化。\n"
        "- 关键事实或数据，例如新客户、复购、流失、成本、KPI 或团队行为。\n"
        "- 你希望优先判断的问题边界，例如客户价值、战略执行、指标体系或组织责任。\n\n"
        "检索质量问题：\n"
        f"{issue_lines}"
    )

    return {
        "final_answer": final_answer,
        "verification": {
            "passed": False,
            "issues": issues,
            "needs_revision": False,
        },
        "trace": append_trace(
            state,
            node="low_confidence",
            output_summary={
                "issues": issues,
            },
        ),
    }


def diagnose_node(state: AgentState) -> dict:
    """
    Build a structured diagnosis frame before report generation.
    """
    problem_types = state.get("problem_types", [])
    retrieved_chunks = state.get("retrieved_chunks", [])
    retrieval_quality = state.get("retrieval_quality", {})

    return {
        "diagnosis_summary": {
            "problem_types": problem_types,
            "primary_problem_type": problem_types[0] if problem_types else "general_management_diagnosis",
            "evidence_count": len(retrieved_chunks),
            "retrieval_quality": retrieval_quality.get("level", "unknown"),
        },
        "trace": append_trace(
            state,
            node="diagnose",
            output_summary={
                "primary_problem_type": problem_types[0] if problem_types else "general_management_diagnosis",
                "evidence_count": len(retrieved_chunks),
                "retrieval_quality": retrieval_quality.get("level", "unknown"),
            },
            next_node="generate",
        ),
    }


def generate_node(state: AgentState) -> dict:
    """
    Generate the first management diagnosis report.
    """
    messages = build_generation_messages(
        company_context=state["company_context"],
        goal=state.get("goal"),
        language=state.get("language", "zh"),
        retrieved_chunks=state.get("retrieved_chunks", []),
        problem_types=state.get("problem_types", []),
        diagnosis_hints=state.get("diagnosis_hints", []),
        diagnosis_summary=state.get("diagnosis_summary", {}),
    )

    report = chat_with_ollama(messages)

    return {
        "report": report,
        "revision_count": state.get("revision_count", 0),
        "trace": append_trace(
            state,
            node="generate",
            output_summary={
                "report_chars": len(report),
            },
            next_node="verify",
        ),
    }


def verify_node(state: AgentState) -> dict:
    """
    Verify whether the generated report is complete and useful.
    """
    verification = verify_report_quality(
        report=state.get("report", ""),
        retrieved_chunks=state.get("retrieved_chunks", []),
    )
    needs_revision = verification.get("needs_revision", False)
    revision_count = state.get("revision_count", 0)
    next_node = "revise" if needs_revision and revision_count < 1 else "memory"

    return {
        "verification": verification,
        "trace": append_trace(
            state,
            node="verify",
            output_summary={
                "passed": verification.get("passed", False),
                "needs_revision": needs_revision,
                "issues": verification.get("issues", []),
            },
            decision=next_node,
            next_node=next_node,
        ),
    }


def revise_node(state: AgentState) -> dict:
    """
    Revise the report if verification fails.
    """
    messages = build_revision_messages(
        company_context=state["company_context"],
        goal=state.get("goal"),
        language=state.get("language", "zh"),
        retrieved_chunks=state.get("retrieved_chunks", []),
        current_report=state.get("report", ""),
        issues=state.get("verification", {}).get("issues", []),
    )

    revised_report = chat_with_ollama(messages)

    return {
        "report": revised_report,
        "revision_count": state.get("revision_count", 0) + 1,
        "trace": append_trace(
            state,
            node="revise",
            output_summary={
                "revision_count": state.get("revision_count", 0) + 1,
                "report_chars": len(revised_report),
            },
            next_node="verify",
        ),
    }


def memory_node(state: AgentState) -> dict:
    """
    Save the final diagnosis record into local project memory.
    """
    final_answer = state.get("report", "")
    updated_state = dict(state)
    updated_state["final_answer"] = final_answer

    project_id = save_project_record(updated_state)

    return {
        "project_id": project_id,
        "final_answer": final_answer,
        "trace": append_trace(
            state,
            node="memory",
            output_summary={
                "project_id": project_id,
                "final_answer_chars": len(final_answer),
            },
        ),
    }
