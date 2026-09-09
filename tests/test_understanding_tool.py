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
