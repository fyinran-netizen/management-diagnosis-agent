from app.rag.retriever import retrieve_relevant_chunks


def test_retrieve_customer_value_chunks():
    query = "增长放缓 新客户减少 顾客价值 客户需求"

    results = retrieve_relevant_chunks(query, top_k=3)

    assert len(results) > 0
    assert any(
        "顾客" in f"{item['title']} {item['content']}"
        or "客户" in f"{item['title']} {item['content']}"
        for item in results
    )


def test_retrieve_metrics_chunks():
    query = "KPI 指标 考核 成本 效率 目标混乱"

    results = retrieve_relevant_chunks(query, top_k=3)

    assert len(results) > 0
    assert any(
        "指标" in f"{item['title']} {item['content']}"
        or "KPI" in f"{item['title']} {item['content']}"
        or "考核" in f"{item['title']} {item['content']}"
        for item in results
    )


def test_retrieve_returns_score_field():
    query = "增长放缓 新客户减少 KPI"

    results = retrieve_relevant_chunks(query, top_k=3)

    assert len(results) > 0
    assert "score" in results[0]
    assert isinstance(results[0]["score"], int | float)
    assert "retrieval_method" in results[0]
    assert "keyword_score" in results[0]
    assert "embedding_score" in results[0]
    assert "hybrid_score" in results[0]


def test_retrieve_uses_private_knowledge_only():
    query = "增长放缓 新客户减少 KPI"

    results = retrieve_relevant_chunks(query, top_k=10)
    sources = {item["source"] for item in results}

    assert sources
    assert "99_private_test.md" not in sources
    assert not any(source.startswith("0") and source.endswith(".md") for source in sources)
