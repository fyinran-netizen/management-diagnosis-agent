from app.tools.understanding import understand_query


def test_rule_based_result_returns_general_diagnosis_hint():
    result = understand_query("A general management diagnosis is needed.")

    assert len(result["diagnosis_hints"]) == 1
    assert "general management diagnosis" in result["diagnosis_hints"][0].lower()
