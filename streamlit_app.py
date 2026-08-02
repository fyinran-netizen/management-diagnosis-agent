from __future__ import annotations

from typing import Any

import streamlit as st

from app.agent.graph import run_diagnosis_workflow
from app.llm.ollama_client import OllamaClientError, get_ollama_config


SAMPLE_DESCRIPTION = (
    "我们公司最近增长放缓，团队每天都很忙，但新客户越来越少。"
    "管理层主要在抓成本和效率，员工只是完成 KPI。"
    "请帮我判断主要管理问题，并给出下一步建议。"
)


def format_score(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{value:.3f}"
    return "-"


def run_diagnosis(description: str) -> dict[str, Any]:
    return run_diagnosis_workflow(description=description)


def render_verification(verification: dict[str, Any], revision_count: int) -> None:
    passed = verification.get("passed", False)
    status = "Passed" if passed else "Needs attention"
    st.metric("Verification", status)
    st.caption(f"Revision count: {revision_count}")

    issues = verification.get("issues", [])
    if issues:
        st.markdown("Issues")
        for issue in issues:
            st.write(f"- {issue}")


def render_trace(trace: list[dict[str, Any]]) -> None:
    if not trace:
        st.info("No trace events yet.")
        return

    for index, event in enumerate(trace, start=1):
        title = event.get("node", f"Step {index}")
        decision = event.get("decision")
        suffix = f" -> {decision}" if decision else ""
        with st.expander(f"{index}. {title}{suffix}", expanded=index <= 3):
            output_summary = event.get("output_summary", {})
            if output_summary:
                st.json(output_summary)
            next_node = event.get("next_node")
            if next_node:
                st.caption(f"Next node: {next_node}")


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        st.info("No retrieved sources.")
        return

    for index, source in enumerate(sources, start=1):
        title = source.get("title") or f"Source {index}"
        source_name = source.get("source", "unknown")
        score = format_score(source.get("score"))
        with st.expander(f"{index}. {title} | {source_name} | score {score}"):
            content = source.get("content")
            if content:
                st.markdown(content)
            else:
                st.caption("No full content returned.")


def main() -> None:
    st.set_page_config(
        page_title="Management Diagnosis Agent",
        page_icon="MD",
        layout="wide",
    )

    st.title("Management Diagnosis Agent")

    base_url, model = get_ollama_config()
    st.caption(f"Local workflow Agent | Ollama model: {model} | Ollama URL: {base_url}")

    if "description" not in st.session_state:
        st.session_state.description = SAMPLE_DESCRIPTION
    if "result" not in st.session_state:
        st.session_state.result = None
    if "error" not in st.session_state:
        st.session_state.error = None

    with st.sidebar:
        st.header("Run")
        description = st.text_area(
            "Case description",
            key="description",
            height=260,
            placeholder="Describe growth, customers, team behavior, metrics, strategy, or organization symptoms...",
        )
        run_clicked = st.button(
            "Run diagnosis",
            type="primary",
            use_container_width=True,
            disabled=len(description.strip()) < 10,
        )
        if st.button("Clear result", use_container_width=True):
            st.session_state.result = None
            st.session_state.error = None

    if run_clicked:
        st.session_state.error = None
        with st.spinner("Running diagnosis workflow..."):
            try:
                st.session_state.result = run_diagnosis(description.strip())
            except OllamaClientError as exc:
                st.session_state.result = None
                st.session_state.error = str(exc)
            except Exception as exc:  # pragma: no cover - UI guardrail
                st.session_state.result = None
                st.session_state.error = f"{type(exc).__name__}: {exc}"

    if st.session_state.error:
        st.error(st.session_state.error)

    result = st.session_state.result
    if not result:
        st.info("Enter a case description and run the diagnosis.")
        return

    report = result.get("final_answer") or result.get("report") or ""
    verification = result.get("verification", {})
    retrieved_sources = result.get("retrieved_chunks", [])
    trace = result.get("trace", [])

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("Diagnosis Report")
        if report:
            st.markdown(report)
        else:
            st.warning("No report was generated.")

    with right:
        render_verification(verification, result.get("revision_count", 0))
        project_id = result.get("project_id")
        if project_id:
            st.caption(f"Project ID: {project_id}")

    st.divider()

    tab_trace, tab_sources, tab_raw = st.tabs(
        ["Agent Timeline", "Retrieved Sources", "Raw State"]
    )
    with tab_trace:
        render_trace(trace)
    with tab_sources:
        render_sources(retrieved_sources)
    with tab_raw:
        st.json(result)


if __name__ == "__main__":
    main()
