from __future__ import annotations

from app.agent.prompts import build_generation_messages, build_revision_messages
from app.agent.state import AgentState
from app.llm.ollama_client import chat_with_ollama
from app.memory.project_memory import save_project_record
from app.rag.retriever import retrieve_relevant_chunks
from app.tools.diagnosis_tools import build_diagnosis_hints
from app.tools.problem_router_tool import route_problem
from app.tools.verify_tool import verify_report_quality
from app.tools.language_tool import detect_output_language


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
    )

    report = chat_with_ollama(messages)

    return {
        "report": report,
        "revision_count": state.get("revision_count", 0),
    }


def verify_node(state: AgentState) -> dict:
    """
    Verify whether the generated report is complete and useful.
    """
    verification = verify_report_quality(
        report=state.get("report", ""),
        retrieved_chunks=state.get("retrieved_chunks", []),
    )

    return {
        "verification": verification,
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
    }