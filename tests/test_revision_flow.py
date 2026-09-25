from app.agent.constants import MAX_REVISIONS
from app.agent.graph import after_validation
from app.agent.nodes import generation_node, validation_node


def test_generation_uses_generate_report_on_first_entry(monkeypatch):
    calls = []
    monkeypatch.setattr("app.agent.nodes.generate_report", lambda **kwargs: calls.append("generate") or "initial")
    monkeypatch.setattr("app.agent.nodes.revise_report", lambda **kwargs: calls.append("revise") or "revised")

    result = generation_node({"description": "context", "revision_count": 0})

    assert result["report"]["core_diagnosis"] == "initial"
    assert result["revision_count"] == 0
    assert calls == ["generate"]


def test_generation_revises_once_after_validation(monkeypatch):
    calls = []
    monkeypatch.setattr("app.agent.nodes.generate_report", lambda **kwargs: calls.append("generate") or "initial")
    monkeypatch.setattr("app.agent.nodes.revise_report", lambda **kwargs: calls.append("revise") or "revised")

    result = generation_node({
        "description": "context",
        "report": {"core_diagnosis": "initial"},
        "verification": {"needs_revision": True, "issues": ["missing basis"]},
        "revision_count": 0,
    })

    assert result["report"]["core_diagnosis"] == "revised"
    assert result["revision_count"] == 1
    assert calls == ["revise"]


def test_validation_only_verifies_and_does_not_revise(monkeypatch):
    monkeypatch.setattr(
        "app.agent.nodes.verify_report_quality",
        lambda report, chunks: {"passed": False, "issues": ["issue"], "needs_revision": True},
    )
    monkeypatch.setattr("app.agent.nodes.revise_report", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not revise in validation")))

    result = validation_node({"report": {"core_diagnosis": "initial"}, "revision_count": 0})

    assert result["verification"]["needs_revision"] is True
    assert "report" not in result
    assert "revision_count" not in result


def test_after_validation_allows_at_most_one_revision():
    assert after_validation({"verification": {"needs_revision": True}, "revision_count": 0}) == "generation"
    assert after_validation({"verification": {"needs_revision": True}, "revision_count": MAX_REVISIONS}) == "persistence"
    assert after_validation({"verification": {"needs_revision": False}, "revision_count": 0}) == "persistence"
