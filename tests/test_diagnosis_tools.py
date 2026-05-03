from app.tools.diagnosis_tools import build_diagnosis_hints


def test_build_diagnosis_hints_for_known_problem_type():
    result = build_diagnosis_hints(["customer_value_misalignment"])

    assert len(result) == 1
    assert "core customers" in result[0] or "customer value" in result[0]


def test_build_diagnosis_hints_for_empty_input():
    result = build_diagnosis_hints([])

    assert len(result) == 1
    assert "general management diagnosis" in result[0].lower()


def test_build_diagnosis_hints_for_unknown_type_uses_general_hint():
    result = build_diagnosis_hints(["unknown_problem_type"])

    assert len(result) == 1
    assert "general management diagnosis" in result[0].lower()