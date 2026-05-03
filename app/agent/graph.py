from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    intake_node,
    route_node,
    generate_node,
    memory_node,
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


def build_diagnosis_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("intake", intake_node)
    workflow.add_node("route", route_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("revise", revise_node)
    workflow.add_node("memory", memory_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "route")
    workflow.add_edge("route", "retrieve")
    workflow.add_edge("retrieve", "generate")
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