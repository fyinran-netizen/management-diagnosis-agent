from app.tools.understanding import understand_query


def test_raw_mode_uses_input_as_retrieval_query():
    result = understand_query("customer growth is slowing", mode="raw")

    assert result["raw_query"] == "customer growth is slowing"
    assert result["retrieval_query"] == result["raw_query"]
    assert result["mode"] == "raw"
    assert result["problem_types"] == []
    assert result["diagnosis_hints"] == []


def test_rule_based_mode_preserves_prepared_query_structure():
    result = understand_query(
        "A management diagnosis is needed.",
        mode="rule_based",
        goal="Provide practical recommendations.",
    )

    assert result["retrieval_query"].startswith(
        "A management diagnosis is needed.\nProvide practical recommendations.\n"
    )
    assert result["problem_types"]
    assert result["diagnosis_hints"]


def test_rewrite_mode_uses_only_raw_query_and_returns_no_diagnosis_metadata(monkeypatch):
    captured = {}

    def fake_chat(messages, model):
        captured["messages"] = messages
        captured["model"] = model
        return "团队增长放缓，分析市场竞争与组织能力约束"

    monkeypatch.setattr(
        "app.tools.understanding.strategies.rewrite.strategy.chat_with_ollama",
        fake_chat,
    )

    result = understand_query(
        "呃，我们最近增长有点慢，想知道是不是市场竞争或者组织能力的问题？",
        mode="rewrite",
        goal="This must not be sent to rewrite.",
    )

    assert result["mode"] == "rewrite"
    assert result["retrieval_query"] == "团队增长放缓，分析市场竞争与组织能力约束"
    assert result["problem_types"] == []
    assert result["diagnosis_hints"] == []
    assert len(captured["messages"]) == 2
    assert "This must not be sent to rewrite." not in str(captured["messages"])
