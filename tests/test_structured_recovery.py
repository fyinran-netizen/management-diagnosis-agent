import json

from app.agent.nodes import generation_node
from app.tools.generation.generator import (
    _strict_parse_section,
    generate_diagnosis_report,
    get_last_generation_section_metrics,
)
from app.tools.generation.recovery import recover_section_json
from app.tools.generation.schemas import assemble_report_section
from app.tools.validation import validate_generation_report


def section(text="text", source_items=None):
    return {"sentences": [{"text": text, "source_items": source_items or []}], "content": text, "source_items": source_items or []}


def test_recovery_cases_are_programmatic_and_conservative():
    valid = '{"sentences":[{"text":"x","source_items":[1]}]}'
    assert recover_section_json(valid).success is True
    assert recover_section_json("```json\n" + valid + "\n```").actions == ["strip_code_fence"]
    assert recover_section_json("Explanation: " + valid + " done").success is True
    normalized = recover_section_json('{"sentences":[{"text":"x","source_items":"1"}]}')
    assert normalized.success is True
    assert normalized.value["sentences"][0]["source_items"] == [1]
    assert recover_section_json('{"sentences":[{"text":"x"}]}').success is False
    assert recover_section_json('{"sentences":[{"text":"truncated"}').success is False
    assert recover_section_json('{"sentences":[]}').success is False


def test_duplicate_sentences_key_is_strict_parse_failure_and_not_recovered():
    duplicate = (
        '{"sentences":[{"text":"old","source_items":[]}],'
        '"sentences":[{"text":"new","source_items":[]}]}'
    )
    parsed, success = _strict_parse_section(duplicate)
    assert success is False
    assert parsed["sentences"] == []
    assert recover_section_json(duplicate).success is False

    outputs = iter([
        duplicate,
        '{"sentences":[{"text":"m","source_items":[]}]}',
        '{"sentences":[{"text":"r","source_items":[]}]}',
        '{"sentences":[{"text":"a","source_items":[]}]}',
    ])
    generate_diagnosis_report(
        description="d", problem_types=[], retrieved_chunks=[],
        llm=lambda messages, model: next(outputs),
    )
    metrics = get_last_generation_section_metrics()
    assert metrics["core_diagnosis"]["final_parse_success"] is False
    assert metrics["core_diagnosis"]["recovery_success"] is False


def test_generate_section_metrics_distinguish_initial_and_recovered_parse():
    outputs = iter([
        '```json\n{"sentences":[{"text":"x","source_items":[]}]}' + '\n```',
        '{"sentences":[{"text":"y","source_items":[]}]}' ,
        '{"sentences":[{"text":"z","source_items":[]}]}' ,
        '{"sentences":[{"text":"r","source_items":[]}]}' ,
    ])

    result = generate_diagnosis_report(
        description="d", problem_types=[], retrieved_chunks=[],
        llm=lambda messages, model: next(outputs),
    )
    metrics = get_last_generation_section_metrics()
    assert result["report"]["core_diagnosis"]["content"] == "x"
    assert metrics["core_diagnosis"]["initial_parse_success"] is False
    assert metrics["core_diagnosis"]["final_parse_success"] is True
    assert metrics["core_diagnosis"]["recovery_success"] is True
    assert metrics["management_concepts"]["recovery_attempted"] is False


def test_validation_reports_failed_sections_without_parsing_issue_text():
    report = {name: section(name) for name in ("core_diagnosis", "management_concepts", "root_causes", "recommendations")}
    report["root_causes"] = section("")
    metrics = {name: {"done_reason": "stop", "final_parse_success": True} for name in report}
    result = validate_generation_report(report, [], metrics)
    assert result["failed_sections"] == ["root_causes"]


def test_validation_does_not_fail_recovered_section_on_initial_parse_metric():
    report = {name: section(name) for name in ("core_diagnosis", "management_concepts", "root_causes", "recommendations")}
    metrics = {
        name: {"done_reason": "stop", "initial_parse_success": True, "final_parse_success": True}
        for name in report
    }
    metrics["core_diagnosis"].update({"initial_parse_success": False, "recovery_success": True})
    result = validate_generation_report(report, [], metrics)
    assert result["passed"] is True
    assert result["failed_sections"] == []


def test_targeted_regeneration_preserves_successful_sections(monkeypatch):
    old = {name: section(name) for name in ("core_diagnosis", "management_concepts", "root_causes", "recommendations")}
    calls = []
    def fake_generate(**kwargs):
        calls.append(kwargs["sections_to_generate"])
        updated = dict(kwargs["existing_report"])
        updated["root_causes"] = section("new root")
        return {"report": updated, "missing_information": []}
    monkeypatch.setattr("app.agent.nodes.generate_diagnosis_report", fake_generate)
    result = generation_node({
        "description": "d", "report": old,
        "verification": {"needs_revision": True, "failed_sections": ["root_causes"]},
        "revision_count": 0,
    })
    assert calls == [["root_causes"]]
    assert result["report"]["core_diagnosis"] is old["core_diagnosis"]
    assert result["report"]["recommendations"] is old["recommendations"]
    assert result["report"]["root_causes"]["content"] == "new root"


def test_targeted_regeneration_passes_multiple_failed_sections(monkeypatch):
    old = {name: section(name) for name in ("core_diagnosis", "management_concepts", "root_causes", "recommendations")}
    calls = []
    def fake_generate(**kwargs):
        calls.append(kwargs["sections_to_generate"])
        return {"report": kwargs["existing_report"], "missing_information": []}
    monkeypatch.setattr("app.agent.nodes.generate_diagnosis_report", fake_generate)
    generation_node({
        "description": "d", "report": old,
        "verification": {"needs_revision": True, "failed_sections": ["management_concepts", "recommendations"]},
        "revision_count": 0,
    })
    assert calls == [["management_concepts", "recommendations"]]


def test_targeted_generation_replaces_failed_section_without_merging():
    old = {
        name: section(f"old {name}", [1])
        for name in ("core_diagnosis", "management_concepts", "root_causes", "recommendations")
    }
    outputs = iter(['{"sentences":[{"text":"new root","source_items":[]}]}'])
    result = generate_diagnosis_report(
        description="d", problem_types=[], retrieved_chunks=[],
        existing_report=old,
        sections_to_generate=["root_causes"],
        llm=lambda messages, model: next(outputs),
    )
    assert result["report"]["root_causes"]["content"] == "new root"
    assert result["report"]["root_causes"]["source_items"] == []
    assert result["report"]["core_diagnosis"] is old["core_diagnosis"]
    assert result["report"]["management_concepts"] is old["management_concepts"]
    assert result["report"]["recommendations"] is old["recommendations"]
