from app.tools.retrieval.tool import retrieve_relevant_chunks
from app.tools.retrieval.retrievers.hybrid_retriever_rrf import hybrid_retrieve_rrf
from app.tools.retrieval.retrievers.embedding_metadata_retriever import retrieve_by_embedding_metadata


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
    assert "bm25_score" in results[0]
    assert "embedding_score" in results[0]
    assert "embedding_cosine_score" in results[0]
    assert "normalized_keyword_score" in results[0]
    assert "normalized_embedding_score" in results[0]
    assert "hybrid_score" in results[0]
    assert results[0]["rank"] == 1


def test_retrieve_uses_private_knowledge_only():
    query = "增长放缓 新客户减少 KPI"

    results = retrieve_relevant_chunks(query, top_k=10)
    sources = {item["source"] for item in results}

    assert sources
    assert "99_private_test.md" not in sources
    assert not any(source.startswith("0") and source.endswith(".md") for source in sources)


def test_rrf_hybrid_retriever_returns_score_fields():
    query = "澧為暱鏀剧紦 鏂板鎴峰噺灏?KPI"

    results = hybrid_retrieve_rrf(query, top_k=3)

    assert len(results) > 0
    assert "score" in results[0]
    assert isinstance(results[0]["score"], int | float)
    assert "retrieval_method" in results[0]
    assert "keyword_score" in results[0]
    assert "bm25_score" in results[0]
    assert "embedding_score" in results[0]
    assert "embedding_cosine_score" in results[0]
    assert "hybrid_score" in results[0]
    assert "rrf_score" in results[0]
    assert "keyword_rank" in results[0]
    assert "embedding_rank" in results[0]
    assert results[0]["rank"] == 1


def test_metadata_embedding_retriever_uses_separate_index():
    results = retrieve_by_embedding_metadata("KPI 鎸囨爣 鐩爣", top_k=3)

    assert len(results) == 3
    assert results[0]["retrieval_method"] == "embedding_metadata"
    assert results[0]["rank"] == 1
    assert "embedding_cosine_score" in results[0]
