from app.agent.nodes import retrieval_node, understanding_node
from app.tools.understanding import understand_query
from app.tools.retrieval.retrieval_observation import build_retrieval_observation


def test_problem_check_is_returned_by_unified_interface():
    result = understand_query("help")

    assert result["problem_check"]["is_clear"] is False
    assert result["problem_check"]["questions"]


def test_understanding_node_uses_default_production_strategy():
    result = understanding_node({"description": "A general management diagnosis is needed."})

    assert result["retrieval_query"]


def test_retrieval_node_consumes_prepared_query(monkeypatch):
    queries = []
    monkeypatch.setattr(
        "app.agent.nodes.retrieve_relevant_chunks",
        lambda query, top_k: queries.append((query, top_k)) or [],
    )

    retrieval_node({"retrieval_query": "prepared query"})

    assert queries == [("prepared query", 5)]


def test_retrieval_quality_flags_empty_results():
    result = build_retrieval_observation([])

    assert result["status"] == "observation"
    assert result["chunk_count"] == 0
