from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    clarification_node,
    diagnose_node,
    intake_node,
    low_confidence_node,
    problem_check_node,
    route_node,
    generate_node,
    memory_node,
    retrieval_check_node,
    retrieve_node,
    revise_node,
    verify_node,
)
from app.agent.state import AgentState


MAX_REVISIONS = 1


def should_revise(state: AgentState) -> str:
    verification = state.get("verification", {})
    needs_revision = verification.get("needs_revision", False)
    revision_count = state.get("revision_count", 0)

    if needs_revision and revision_count < MAX_REVISIONS:
        return "revise"

    return "memory"


def should_clarify(state: AgentState) -> str:
    problem_check = state.get("problem_check", {})
    if not problem_check.get("is_clear", False):
        return "clarify"
    return "route"


def should_generate_from_retrieval(state: AgentState) -> str:
    retrieval_quality = state.get("retrieval_quality", {})
    if not retrieval_quality.get("passed", False):
        return "low_confidence"
    return "diagnose"


def build_diagnosis_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("intake", intake_node)
    workflow.add_node("problem_check", problem_check_node)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("route", route_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("retrieval_check", retrieval_check_node)
    workflow.add_node("low_confidence", low_confidence_node)
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("revise", revise_node)
    workflow.add_node("memory", memory_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "problem_check")
    workflow.add_conditional_edges(
        "problem_check",
        should_clarify,
        {
            "clarify": "clarification",
            "route": "route",
        },
    )
    workflow.add_edge("route", "retrieve")
    workflow.add_edge("retrieve", "retrieval_check")
    workflow.add_conditional_edges(
        "retrieval_check",
        should_generate_from_retrieval,
        {
            "low_confidence": "low_confidence",
            "diagnose": "diagnose",
        },
    )
    workflow.add_edge("diagnose", "generate")
    workflow.add_edge("generate", "verify")

    workflow.add_conditional_edges(
        "verify",
        should_revise,
        {
            "revise": "revise",
            "memory": "memory",
        },
    )

    workflow.add_edge("revise", "verify")
    workflow.add_edge("memory", END)
    workflow.add_edge("clarification", END)
    workflow.add_edge("low_confidence", END)

    return workflow.compile()


diagnosis_graph = build_diagnosis_graph()


def run_diagnosis_workflow(
    description: str,
) -> AgentState:
    initial_state: AgentState = {
        "description": description,
        "revision_count": 0,
    }

    return diagnosis_graph.invoke(initial_state)
