from __future__ import annotations

import os

# Keep Transformers output quiet before importing app modules.
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import streamlit as st
from transformers import logging as transformers_logging

from app.core.logging import configure_logging

from app.frontend.components import (
    render_checkpoint_history,
    render_current_state,
    render_graph_visualization,
    render_report,
    render_retrieval,
    render_state_summary,
)

from app.frontend.controls import (
    branch_selected_checkpoint,
    initialize_session_state,
    render_run_controls,
    resume_selected_checkpoint,
)


transformers_logging.set_verbosity_error()
transformers_logging.disable_progress_bar()


SAMPLE_DESCRIPTION = (
    "我们公司过去三个月新客户数量持续下降，销售转化率也在下滑。与此同时，管理层为了降本增效增加了 KPI 考核和审批流程，员工每天都很忙，但主动性明显下降，很多人只完成指标、不愿承担额外责任。我们想判断目前主要的管理问题是什么，以及应该优先调整 KPI、流程还是团队管理方式。"
)


def main() -> None:
    configure_logging()

    st.set_page_config(
        page_title="Drucker Diagnosis Debugger",
        page_icon="D",
        layout="wide",
    )

    initialize_session_state()

    st.title("Drucker Diagnosis Debugger")
    st.caption(
        "LangGraph checkpoint-based step execution and state inspection"
    )

    with st.sidebar:
        st.header("Run Control")

        description = st.text_area(
            "Case Description",
            value=SAMPLE_DESCRIPTION,
            height=240,
        )

        render_run_controls(description)

        st.divider()

        st.header("Graph")
        render_graph_visualization()

    if st.session_state.runtime_error:
        st.error(st.session_state.runtime_error)

    snapshot = st.session_state.current_state

    if snapshot is None:
        st.info(
            "Create a new run to execute the Understanding node."
        )
        return

    render_state_summary(snapshot)

    tab_state, tab_report, tab_retrieval, tab_history = st.tabs(
        [
            "Current State",
            "Report",
            "Retrieval",
            "Checkpoints",
        ]
    )

    with tab_state:
        render_current_state(snapshot)

    with tab_report:
        render_report(snapshot)

    with tab_retrieval:
        render_retrieval(snapshot)

    with tab_history:
        checkpoint_id = render_checkpoint_history(
            st.session_state.state_history
        )
        st.session_state.selected_checkpoint_id = checkpoint_id

        if checkpoint_id:
            resume_col, branch_col = st.columns(2)
            with resume_col:
                if st.button(
                    "Resume (Original Run)",
                    use_container_width=True,
                    help="Continue the original run from this checkpoint.",
                ):
                    resume_selected_checkpoint(checkpoint_id)
                    st.rerun()
            with branch_col:
                if st.button(
                    "Branch From Checkpoint",
                    use_container_width=True,
                    help="Create a new run from this checkpoint.",
                ):
                    branch_selected_checkpoint(checkpoint_id)
                    st.rerun()


if __name__ == "__main__":
    main()
