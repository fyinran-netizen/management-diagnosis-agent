from __future__ import annotations

import streamlit as st

from app.agent.runtime import (
    branch_from_checkpoint,
    get_current_state,
    get_state_history,
    load_run,
    resume_from_checkpoint,
    run_next_step,
    start_run,
)


def initialize_session_state() -> None:
    defaults = {
        "run_id": None,
        "current_state": None,
        "state_history": [],
        "selected_checkpoint_id": None,
        "runtime_error": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def refresh_run_state() -> None:
    run_id = st.session_state.run_id
    if not run_id:
        return

    st.session_state.current_state = get_current_state(run_id)
    st.session_state.state_history = get_state_history(run_id)


def load_existing_run(run_id: str) -> None:
    st.session_state.runtime_error = None
    run_id = run_id.strip()
    if not run_id:
        return

    try:
        current_state, state_history = load_run(run_id)
        st.session_state.run_id = run_id
        st.session_state.current_state = current_state
        st.session_state.state_history = state_history
        st.session_state.selected_checkpoint_id = None
    except Exception as exc:
        st.session_state.runtime_error = f"{type(exc).__name__}: {exc}"


def start_new_run(description: str) -> None:
    st.session_state.runtime_error = None

    try:
        run_id = start_run(description)
        st.session_state.run_id = run_id
        st.session_state.selected_checkpoint_id = None
        refresh_run_state()
    except Exception as exc:
        st.session_state.runtime_error = f"{type(exc).__name__}: {exc}"


def execute_next_step() -> None:
    run_id = st.session_state.run_id
    if not run_id:
        return

    st.session_state.runtime_error = None

    try:
        run_next_step(run_id)
        refresh_run_state()
    except Exception as exc:
        st.session_state.runtime_error = f"{type(exc).__name__}: {exc}"


def resume_selected_checkpoint(checkpoint_id: str) -> None:
    run_id = st.session_state.run_id
    if not run_id or not checkpoint_id:
        return

    st.session_state.runtime_error = None

    try:
        resume_from_checkpoint(
            run_id=run_id,
            checkpoint_id=checkpoint_id,
        )
        refresh_run_state()
    except Exception as exc:
        st.session_state.runtime_error = f"{type(exc).__name__}: {exc}"


def branch_selected_checkpoint(checkpoint_id: str) -> None:
    source_run_id = st.session_state.run_id
    if not source_run_id or not checkpoint_id:
        return

    st.session_state.runtime_error = None

    try:
        new_run_id = branch_from_checkpoint(
            source_run_id=source_run_id,
            checkpoint_id=checkpoint_id,
        )
        st.session_state.run_id = new_run_id
        st.session_state.selected_checkpoint_id = None
        refresh_run_state()
    except Exception as exc:
        st.session_state.runtime_error = f"{type(exc).__name__}: {exc}"


def render_run_controls(description: str) -> None:
    col_new, col_next = st.columns(2)

    with col_new:
        if st.button(
            "New Run",
            type="primary",
            use_container_width=True,
            disabled=not description.strip(),
        ):
            start_new_run(description.strip())

    with col_next:
        if st.button(
            "Next Step",
            use_container_width=True,
            disabled=not bool(st.session_state.run_id),
        ):
            execute_next_step()

    run_id_input = st.text_input(
        "Run ID",
        value=st.session_state.run_id or "",
        key="run_id_input",
        placeholder="Paste an existing run ID",
    )
    if st.button(
        "Load Run",
        use_container_width=True,
        disabled=not run_id_input.strip(),
    ):
        load_existing_run(run_id_input)
        st.rerun()

    if st.session_state.run_id:
        st.caption(f"Run ID: {st.session_state.run_id}")
