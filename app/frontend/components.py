from __future__ import annotations

import html
import base64
from typing import Any

import streamlit as st

from app.agent.graph import diagnosis_graph
from app.tools.generation.sources import resolve_source_items


def _checkpoint_id(snapshot: Any) -> str | None:
    config = getattr(snapshot, "config", None) or {}
    return (config.get("configurable", {}) or {}).get("checkpoint_id")


def render_current_state(snapshot: Any) -> None:
    st.subheader("Current State")
    if snapshot is None:
        st.info("No active run.")
        return
    values = getattr(snapshot, "values", {}) or {}
    left, right = st.columns(2)
    with left:
        checkpoint_id = _checkpoint_id(snapshot)
        st.metric("Checkpoint", checkpoint_id[:12] + "..." if checkpoint_id and len(checkpoint_id) > 12 else checkpoint_id or "-")
    with right:
        next_nodes = list(getattr(snapshot, "next", ()) or ())
        st.metric("Next Node", ", ".join(next_nodes) if next_nodes else "END")
    st.json(values)


def render_state_summary(snapshot: Any) -> None:
    if snapshot is None:
        return
    values = getattr(snapshot, "values", {}) or {}
    cols = st.columns(4)
    cols[0].metric("Next", ", ".join(getattr(snapshot, "next", ()) or ()) or "END")
    cols[1].metric("Revision", values.get("revision_count", 0))
    cols[2].metric("Retrieved", len(values.get("retrieved_chunks", [])))
    passed = (values.get("verification", {}) or {}).get("passed")
    cols[3].metric("Validation", "Passed" if passed is True else "Failed" if passed is False else "-")


def render_checkpoint_history(history: list[Any]) -> str | None:
    st.subheader("Checkpoint History")
    if not history:
        st.info("No checkpoints yet.")
        return None
    mapping: dict[str, Any] = {}
    for index, snapshot in enumerate(history):
        checkpoint_id = _checkpoint_id(snapshot)
        if checkpoint_id:
            mapping[f"{index + 1}. {checkpoint_id[:12]}..."] = snapshot
    if not mapping:
        st.info("No checkpoint IDs available.")
        return None
    selected = st.selectbox("Select checkpoint", list(mapping))
    snapshot = mapping[selected]
    with st.expander("Checkpoint details", expanded=True):
        st.caption(f"Checkpoint ID: {_checkpoint_id(snapshot)}")
        st.json(getattr(snapshot, "values", {}) or {})
    return _checkpoint_id(snapshot)


def _section_sentences(section: dict[str, Any]) -> list[dict[str, Any]]:
    sentences = section.get("sentences")
    if isinstance(sentences, list):
        return sentences
    content = section.get("content")
    if isinstance(content, str) and content:
        return [{"text": content, "source_items": section.get("source_items", [])}]
    return []


def _render_user_sentences_with_citations(sentences: Any, retrieved_chunks: list[dict[str, Any]] | None) -> None:
    """Render one continuous paragraph; citations follow sentence order, never text matching."""
    if not isinstance(sentences, list):
        return
    parts: list[str] = []
    for sentence in sentences:
        if not isinstance(sentence, dict):
            continue
        text = sentence.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        parts.append(html.escape(text.strip()))
        sources = resolve_source_items(sentence.get("source_items", []), retrieved_chunks or [])
        if not sources:
            continue
        source_markup = "".join(
            '<div class="diagnosis-citation-source">'
            f"<div>第{html.escape(source['chapter_number'])}章 · 第{html.escape(source['section_number'])}节</div>"
            f"<div>知识摘要：{html.escape(source['summary'] or '暂无知识摘要。')}</div>"
            "</div>"
            for source in sources
        )
        parts.append(
            '<details class="diagnosis-citation">'
            '<summary aria-label="查看来源">ⓘ</summary>'
            f'<div class="diagnosis-citation-popover">{source_markup}</div>'
            "</details>"
        )
    if not parts:
        return
    st.markdown(
        "<style>"
        ".diagnosis-inline-paragraph{line-height:1.8;}"
        ".diagnosis-citation{display:inline-block;margin-left:.2em;vertical-align:baseline;position:relative;}"
        ".diagnosis-citation summary{cursor:pointer;list-style:none;color:#6b7280;font-size:.85em;}"
        ".diagnosis-citation summary::-webkit-details-marker{display:none;}"
        ".diagnosis-citation-popover{position:absolute;z-index:10;left:0;top:1.4em;width:280px;padding:.7em;background:white;border:1px solid #ddd;border-radius:.5em;box-shadow:0 4px 16px #0002;}"
        ".diagnosis-citation-source+.diagnosis-citation-source{border-top:1px solid #eee;margin-top:.6em;padding-top:.6em;}"
        "</style>"
        f'<div class="diagnosis-inline-paragraph">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_diagnosis_report(report: Any) -> None:
    if not isinstance(report, dict):
        st.markdown(str(report))
        return
    labels = {"core_diagnosis": "Core diagnosis", "management_concepts": "Management concepts", "root_causes": "Root causes", "recommendations": "Recommendations", "missing_information": "Missing information"}
    chunks = st.session_state.get("_diagnosis_retrieved_chunks", [])
    for key, label in labels.items():
        value = report.get(key)
        if not value:
            continue
        st.markdown(f"**{label}**")
        if isinstance(value, dict) and ("sentences" in value or "content" in value):
            _render_user_sentences_with_citations(_section_sentences(value), chunks)
        elif isinstance(value, list):
            for item in value:
                st.markdown(f"- {item}")
        else:
            st.write(value)


def render_report(snapshot: Any) -> None:
    if snapshot is None:
        return
    values = getattr(snapshot, "values", {}) or {}
    st.session_state["_diagnosis_retrieved_chunks"] = values.get("retrieved_chunks", [])
    st.subheader("Diagnosis Report")
    report = values.get("report")
    final_answer = values.get("final_answer")
    if report:
        st.markdown("**Report**")
        _render_diagnosis_report(report)
    if final_answer:
        st.markdown("**Final answer**")
        _render_diagnosis_report(final_answer)
    if not report and not final_answer:
        st.info("No report generated at this step.")


def render_user_report(report: Any, retrieved_chunks: list[dict[str, Any]] | None) -> None:
    st.divider()
    st.subheader("用户报告预览 · User-facing Diagnosis Report")
    if not isinstance(report, dict):
        st.info("No structured diagnosis report is available.")
        return
    sections = (("core_diagnosis", "核心诊断"), ("management_concepts", "相关管理概念"), ("root_causes", "根因分析"), ("recommendations", "改进建议"))
    rendered = False
    for key, label in sections:
        section = report.get(key)
        if not isinstance(section, dict):
            continue
        sentences = _section_sentences(section)
        if not sentences:
            continue
        rendered = True
        st.markdown(f"**{label}**")
        _render_user_sentences_with_citations(sentences, retrieved_chunks)
    if not rendered:
        st.info("No structured diagnosis sections are available.")


def render_retrieval(snapshot: Any) -> None:
    if snapshot is None:
        return
    values = getattr(snapshot, "values", {}) or {}
    chunks = values.get("retrieved_chunks", [])
    st.subheader("Retrieval")
    if values.get("retrieval_quality"):
        st.markdown("**Retrieval Quality**")
        st.json(values["retrieval_quality"])
    if not chunks:
        st.info("No retrieved chunks at this step.")
        return
    for index, chunk in enumerate(chunks, start=1):
        with st.expander(chunk.get("title") or f"Chunk {index}"):
            st.write(chunk.get("content", ""))


def render_debug_value(snapshot: Any, key: str, title: str) -> None:
    if snapshot is None:
        return
    value = (getattr(snapshot, "values", {}) or {}).get(key)
    st.subheader(title)
    if value in (None, "", [], {}):
        st.info(f"No {title.lower()} at this step.")
    elif isinstance(value, str):
        st.code(value, language="text")
    else:
        st.json(value)


def render_graph_visualization() -> None:
    st.subheader("Graph")
    try:
        mermaid_source = diagnosis_graph.get_graph().draw_mermaid()
        graph_html = f"""
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                min-height: 600px;
                overflow: hidden;
                background: transparent;
              }}
              .mermaid {{
                width: 100%;
                min-height: 600px;
                display: flex;
                align-items: flex-start;
                justify-content: center;
              }}
              .mermaid svg {{
                display: block;
                max-width: 100%;
                height: auto;
              }}
            </style>
          </head>
          <body>
            <div class="mermaid">{mermaid_source}</div>
            <script type="module">
              import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
              mermaid.initialize({{
                startOnLoad: false,
                securityLevel: "strict",
                theme: "default",
                flowchart: {{ useMaxWidth: true, htmlLabels: true }}
              }});
              await mermaid.run({{ querySelector: ".mermaid" }});
            </script>
          </body>
        </html>
        """
        iframe_src = "data:text/html;base64," + base64.b64encode(graph_html.encode("utf-8")).decode("ascii")
        st.iframe(iframe_src, width=1400, height=620)
    except Exception as exc:
        st.caption(f"Graph visualization unavailable: {exc}")
