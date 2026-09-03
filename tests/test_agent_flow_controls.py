from app.agent.graph import run_diagnosis_workflow
from app.tools.understanding.problem_check import check_problem_clarity
from app.tools.retrieval.quality import evaluate_retrieval_quality


def test_problem_check_flags_unclear_input():
    result = check_problem_clarity("帮我看看")

    assert result["is_clear"] is False
    assert result["questions"]


def test_problem_check_accepts_specific_management_input():
    result = check_problem_clarity(
        "公司增长放缓，新客户减少，团队每天都很忙，但大家只盯KPI和成本效率。"
    )

    assert result["is_clear"] is True
    assert "增长" in result["signal_terms"]
    assert "KPI" in result["signal_terms"]


def test_retrieval_quality_flags_empty_results():
    result = evaluate_retrieval_quality([])

    assert result["status"] == "observation"
    assert result["chunk_count"] == 0
    assert "passed" not in result
    assert "level" not in result


def test_retrieval_quality_records_observation_without_confidence_or_gate():
    result = evaluate_retrieval_quality(
        [
            {"score": 0.8, "embedding_score": 0.7},
            {"score": 0.4, "embedding_score": 0.6},
        ]
    )

    assert result["status"] == "observation"
    assert result["top_score"] == 0.8
    assert len(result["chunks"]) == 2
    assert "passed" not in result
    assert "level" not in result


def test_workflow_returns_clarification_for_unclear_input():
    result = run_diagnosis_workflow("帮我看看")

    assert "请先补充以下信息" in result["final_answer"]
    assert result["verification"]["needs_revision"] is False
    assert "retrieved_chunks" not in result
