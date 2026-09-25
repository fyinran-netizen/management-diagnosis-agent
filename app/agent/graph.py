from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.checkpoints import checkpoint_saver
from app.agent.constants import MAX_REVISIONS
from app.agent.nodes import (
    generation_node,
    persistence_node,
    retrieval_node,
    understanding_node,
    validation_node,
)
from app.agent.state import AgentState


def after_understanding(state: AgentState) -> str:
    return (
        "retrieval"
        if state.get("intake_validation", {}).get("valid", False)
        else "end"
    )


def after_validation(state: AgentState) -> str:
    needs_revision = state.get("verification", {}).get(
        "needs_revision",
        False,
    )
    revision_count = state.get("revision_count", 0)

    return (
        "generation"
        if needs_revision and revision_count < MAX_REVISIONS
        else "persistence"
    )


workflow = StateGraph(AgentState)

workflow.add_node("understanding", understanding_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("generation", generation_node)
workflow.add_node("validation", validation_node)
workflow.add_node("persistence", persistence_node)

workflow.add_edge(START, "understanding")

workflow.add_conditional_edges(
    "understanding",
    after_understanding,
    {
        "retrieval": "retrieval",
        "end": END,
    },
)

workflow.add_edge("retrieval", "generation")
workflow.add_edge("generation", "validation")

workflow.add_conditional_edges(
    "validation",
    after_validation,
    {
        "generation": "generation",
        "persistence": "persistence",
    },
)

workflow.add_edge("persistence", END)


diagnosis_graph = workflow.compile(
    checkpointer=checkpoint_saver,
    interrupt_after=[
        "understanding",
        "retrieval",
        "generation",
        "validation",
        "persistence",
    ],
)
