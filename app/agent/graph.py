from __future__ import annotations
from langgraph.graph import END, START, StateGraph
from app.agent.nodes import generation_node, persistence_node, retrieval_node, understanding_node, validation_node
from app.agent.state import AgentState
from app.core.logging import get_logger
from time import perf_counter

logger = get_logger("workflow")

def after_understanding(state: AgentState) -> str:
    return "retrieval" if state.get("problem_check", {}).get("is_clear", False) else "end"
def after_retrieval(state: AgentState) -> str:
    return "generation"
def after_validation(state: AgentState) -> str:
    return "generation" if state.get("verification", {}).get("needs_revision", False) and state.get("revision_count", 0) < 1 else "persistence"

workflow = StateGraph(AgentState)
workflow.add_node("understanding", understanding_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("generation", generation_node)
workflow.add_node("validation", validation_node)
workflow.add_node("persistence", persistence_node)
workflow.add_edge(START, "understanding")
workflow.add_conditional_edges("understanding", after_understanding, {"retrieval": "retrieval", "end": END})
workflow.add_conditional_edges("retrieval", after_retrieval, {"generation": "generation", "end": END})
workflow.add_edge("generation", "validation")
workflow.add_conditional_edges("validation", after_validation, {"generation": "generation", "persistence": "persistence"})
workflow.add_edge("persistence", END)
diagnosis_graph = workflow.compile()

def run_diagnosis_workflow(description: str) -> AgentState:
    started_at = perf_counter()
    logger.info("workflow start description_chars=%d", len(description.strip()))
    try:
        result = diagnosis_graph.invoke({"description": description, "revision_count": 0})
    except Exception as exc:
        elapsed = perf_counter() - started_at
        logger.error("workflow exception elapsed_seconds=%.3f error=%s", elapsed, str(exc)[:500])
        raise
    logger.info(
        "workflow completed elapsed_seconds=%.3f final_answer_chars=%d revision_count=%d",
        perf_counter() - started_at,
        len(result.get("final_answer", "")),
        result.get("revision_count", 0),
    )
    return result
