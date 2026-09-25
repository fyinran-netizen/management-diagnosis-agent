from __future__ import annotations

import os

# Keep Transformers output quiet before importing app modules.
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import streamlit as st
from transformers import logging as transformers_logging

from app.core.logging import configure_logging
from app.tools.understanding.problem_types import (
    PROBLEM_TYPE_CODES,
    PROBLEM_TYPE_LABELS,
)

from app.frontend.components import (
    render_checkpoint_history,
    render_current_state,
    render_debug_value,
    render_graph_visualization,
    render_report,
    render_state_summary,
    render_user_report,
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
        "Structured intake · explicit execution controls · checkpoint inspection"
    )

    st.markdown(
        """
        <style>
        .stApp { background: #f3f5f9; }
        [data-testid="stHeader"] { background: rgba(243,245,249,0.9); }
        div[data-testid="stVerticalBlock"] div[data-testid="stExpander"],
        div[data-testid="stForm"] { border-radius: 12px; }
        .block-container { max-width: 1500px; padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    intake_col, execution_col = st.columns([1.55, 1], gap="large")
    with intake_col:
        st.subheader("Intake")
        problem_types = st.multiselect(
            "Problem types",
            PROBLEM_TYPE_CODES,
            default=["general_management_diagnosis"],
            format_func=PROBLEM_TYPE_LABELS.get,
            help="Select one or more problem types.",
        )
        other_problem_type = None
        if "other" in problem_types:
            other_problem_type = st.text_input(
                "Other problem type",
                placeholder="Describe the additional problem type",
            )
        description = st.text_area(
            "Description *",
            value=SAMPLE_DESCRIPTION,
            height=180,
        )

    with execution_col:
        st.subheader("Execution")
        render_run_controls(description, problem_types, other_problem_type)

    with st.expander("Production graph", expanded=True):
        render_graph_visualization()

    if st.session_state.runtime_error:
        st.error(st.session_state.runtime_error)

    snapshot = st.session_state.current_state

    if snapshot is None:
        st.info(
            "Create a new run to execute the Understanding node."
        )
        return

    st.subheader("Workflow progress")
    render_state_summary(snapshot)

    tab_intake, tab_retrieval, tab_report, tab_verification, tab_final, tab_history = st.tabs(
        [
            "Intake",
            "Retrieval",
            "Report",
            "Verification",
            "Final answer",
            "Checkpoints",
        ]
    )

    with tab_intake:
        render_debug_value(snapshot, "intake_validation", "Intake validation")
        render_debug_value(snapshot, "retrieval_query", "Retrieval query")
        render_current_state(snapshot)

    with tab_retrieval:
        render_debug_value(snapshot, "retrieved_chunks", "Retrieved chunks")
        render_debug_value(snapshot, "retrieval_quality", "Retrieval quality")

    with tab_report:
        render_report(snapshot)

    with tab_verification:
        render_debug_value(snapshot, "verification", "Verification")

    with tab_final:
        render_debug_value(snapshot, "final_answer", "Final answer")
        render_report(snapshot)

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

    report_values = getattr(snapshot, "values", {}) or {}
    user_report = report_values.get("final_answer") or report_values.get("report")
    render_user_report(user_report, report_values.get("retrieved_chunks", []))


if __name__ == "__main__":
    main()
