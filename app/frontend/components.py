from __future__ import annotations

from typing import Any

import streamlit as st

from app.agent.graph import diagnosis_graph


def _checkpoint_id(snapshot: Any) -> str | None:
    config = getattr(snapshot, "config", None) or {}
    configurable = config.get("configurable", {})
    return configurable.get("checkpoint_id")


def render_current_state(snapshot: Any) -> None:
    st.subheader("Current State")

    if snapshot is None:
        st.info("No active run.")
        return

    next_nodes = list(getattr(snapshot, "next", ()) or ())
    values = getattr(snapshot, "values", {}) or {}

    left, right = st.columns(2)

    with left:
        checkpoint_id = _checkpoint_id(snapshot)
        st.metric(
            "Checkpoint",
            checkpoint_id[:12] + "..."
            if checkpoint_id and len(checkpoint_id) > 12
            else checkpoint_id or "-",
        )

    with right:
        st.metric(
            "Next Node",
            ", ".join(next_nodes) if next_nodes else "END",
        )

    st.json(values)


def render_state_summary(snapshot: Any) -> None:
    if snapshot is None:
        return

    values = getattr(snapshot, "values", {}) or {}
    next_nodes = list(getattr(snapshot, "next", ()) or ())

    cols = st.columns(4)

    cols[0].metric(
        "Next",
        ", ".join(next_nodes) if next_nodes else "END",
    )

    cols[1].metric(
        "Revision",
        values.get("revision_count", 0),
    )

    cols[2].metric(
        "Retrieved",
        len(values.get("retrieved_chunks", [])),
    )

    verification = values.get("verification", {})
    passed = verification.get("passed")

    if passed is True:
        verification_text = "Passed"
    elif passed is False:
        verification_text = "Failed"
    else:
        verification_text = "-"

    cols[3].metric(
        "Validation",
        verification_text,
    )


def render_checkpoint_history(history: list[Any]) -> str | None:
    st.subheader("Checkpoint History")

    if not history:
        st.info("No checkpoints yet.")
        return None

    options: list[str] = []
    mapping: dict[str, Any] = {}

    for index, snapshot in enumerate(history):
        checkpoint_id = _checkpoint_id(snapshot)

        if not checkpoint_id:
            continue

        next_nodes = list(getattr(snapshot, "next", ()) or ())
        next_label = ", ".join(next_nodes) if next_nodes else "END"

        label = (
            f"{index + 1}. "
            f"{checkpoint_id[:12]}... "
            f"→ {next_label}"
        )

        options.append(label)
        mapping[label] = snapshot

    if not options:
        st.info("No checkpoint IDs available.")
        return None

    selected_label = st.selectbox("Select checkpoint", options)

    selected_snapshot = mapping[selected_label]
    selected_checkpoint_id = _checkpoint_id(selected_snapshot)

    with st.expander("Checkpoint details", expanded=True):
        created_at = getattr(
            selected_snapshot,
            "created_at",
            None,
        )
        metadata = getattr(
            selected_snapshot,
            "metadata",
            {},
        )
        values = getattr(
            selected_snapshot,
            "values",
            {},
        )

        st.caption(
            f"Checkpoint ID: {selected_checkpoint_id}"
        )

        if created_at:
            st.caption(f"Created: {created_at}")

        st.markdown("**State**")
        st.json(values)

        if metadata:
            st.markdown("**Metadata**")
            st.json(metadata)

    # The caller can pass this ID to either Resume or Branch without needing
    # to inspect the selected snapshot again.
    return selected_checkpoint_id


def render_report(snapshot: Any) -> None:
    if snapshot is None:
        return

    values = getattr(snapshot, "values", {}) or {}

    report = (
        values.get("final_answer")
        or values.get("report")
        or ""
    )

    st.subheader("Diagnosis Report")

    if report:
        st.markdown(report)
    else:
        st.info("No report generated at this step.")


def render_retrieval(snapshot: Any) -> None:
    if snapshot is None:
        return

    values = getattr(snapshot, "values", {}) or {}
    chunks = values.get("retrieved_chunks", [])
    quality = values.get("retrieval_quality", {})

    st.subheader("Retrieval")

    if quality:
        st.markdown("**Retrieval Quality**")
        st.json(quality)

    if not chunks:
        st.info("No retrieved chunks at this step.")
        return

    for index, chunk in enumerate(chunks, start=1):
        title = chunk.get("title") or f"Chunk {index}"
        score = chunk.get("score")

        label = title
        if score is not None:
            label += f" | {score:.4f}"

        with st.expander(label):
            st.caption(
                f"Source: {chunk.get('source', '-')}"
            )
            st.write(chunk.get("content", ""))


def render_graph_visualization() -> None:
    st.subheader("Graph")

    try:
        mermaid = diagnosis_graph.get_graph().draw_mermaid()

        html = f"""
        <div class="mermaid">
        {mermaid}
        </div>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default'
            }});
        </script>
        """

        st.iframe(
            html,
            height=500,
        )

    except Exception as exc:
        st.caption(f"Graph visualization unavailable: {exc}")
