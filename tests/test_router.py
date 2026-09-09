from app.tools.understanding import understand_query


def test_rule_based_result_contains_problem_types_and_hints():
    result = understand_query("A management diagnosis is needed.")

    assert result["mode"] == "rule_based"
    assert result["problem_types"] == ["general_management_diagnosis"]
    assert result["diagnosis_hints"]
