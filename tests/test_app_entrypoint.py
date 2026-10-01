from app.agent import runtime


class FakeGraph:
    def __init__(self):
        self.calls = []

    def invoke(self, values, config):
        self.calls.append((values, config))
        return None


def test_start_run_uses_current_runtime_contract_without_running_ollama(monkeypatch):
    graph = FakeGraph()
    monkeypatch.setattr(runtime, "diagnosis_graph", graph)

    run_id = runtime.start_run(
        "  help me diagnose this management issue  ",
        run_id="test-run",
        problem_types=["coordination"],
        other_problem_type="other",
    )

    assert run_id == "test-run"
    values, config = graph.calls[0]
    assert values == {
        "description": "help me diagnose this management issue",
        "problem_types": ["coordination"],
        "other_problem_type": "other",
        "revision_count": 0,
    }
    assert config["configurable"]["thread_id"] == "test-run"
