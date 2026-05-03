from app.rag.retriever import retrieve_relevant_chunks


def test_retrieve_customer_value_chunks():
    query = "增长放缓 新客户减少 顾客价值 客户需求"

    results = retrieve_relevant_chunks(query, top_k=3)

    assert len(results) > 0
    assert any(item["source"] == "01_customer_value.md" for item in results)


def test_retrieve_metrics_chunks():
    query = "KPI 指标 考核 成本 效率 目标混乱"

    results = retrieve_relevant_chunks(query, top_k=3)

    assert len(results) > 0
    assert any(item["source"] == "04_metrics.md" for item in results)


def test_retrieve_returns_score_field():
    query = "增长放缓 新客户减少 KPI"

    results = retrieve_relevant_chunks(query, top_k=3)

    assert len(results) > 0
    assert "score" in results[0]
    assert isinstance(results[0]["score"], int)