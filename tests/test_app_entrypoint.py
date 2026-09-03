from app.agent.graph import run_diagnosis_workflow


def test_streamlit_workflow_entrypoint_returns_clarification_without_ollama():
    result = run_diagnosis_workflow("甯垜鐪嬬湅")
    assert result["verification"]["needs_revision"] is False
    assert result["final_answer"]
