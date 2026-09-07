from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.agent.graph import diagnosis_graph


def build_config(
    run_id: str,
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    configurable: dict[str, Any] = {
        "thread_id": run_id,
    }

    if checkpoint_id is not None:
        configurable["checkpoint_id"] = checkpoint_id

    return {
        "configurable": configurable,
    }


def start_run(
    description: str,
    run_id: str | None = None,
) -> str:
    run_id = run_id or str(uuid4())

    diagnosis_graph.invoke(
        {
            "description": description.strip(),
            "revision_count": 0,
        },
        config=build_config(run_id),
    )

    return run_id


def run_next_step(run_id: str):
    return diagnosis_graph.invoke(
        None,
        config=build_config(run_id),
    )


def get_current_state(run_id: str):
    return diagnosis_graph.get_state(
        build_config(run_id),
    )


def get_state_history(run_id: str):
    return list(
        diagnosis_graph.get_state_history(
            build_config(run_id),
        )
    )


def load_run(run_id: str):
    """Load the current snapshot and checkpoint history for a run."""
    run_id = run_id.strip()
    if not run_id:
        raise ValueError("run_id is required")

    return get_current_state(run_id), get_state_history(run_id)


def _checkpoint_predecessor(snapshot: Any) -> str:
    """Return the node that produced a checkpoint snapshot.

    The selected snapshot tells us what is next, while its parent snapshot
    tells us which node produced it.  Using that node with update_state lets
    LangGraph schedule the selected snapshot's next node in a new thread.
    """
    parent_config = getattr(snapshot, "parent_config", None)
    if parent_config:
        parent_snapshot = diagnosis_graph.get_state(parent_config)
        parent_next = list(getattr(parent_snapshot, "next", ()) or ())
        if len(parent_next) == 1:
            return parent_next[0]

    # The first checkpoint is the graph input, before the first real node.
    return "__input__"


def branch_from_checkpoint(
    source_run_id: str,
    checkpoint_id: str,
) -> str:
    """Create a new run initialized from a checkpoint in another run."""
    source_run_id = source_run_id.strip()
    checkpoint_id = checkpoint_id.strip()
    if not source_run_id or not checkpoint_id:
        raise ValueError("source_run_id and checkpoint_id are required")

    selected = diagnosis_graph.get_state(
        build_config(source_run_id, checkpoint_id),
    )
    selected_id = (
        getattr(selected, "config", {})
        .get("configurable", {})
        .get("checkpoint_id")
    )
    if selected_id != checkpoint_id:
        raise ValueError(
            f"Checkpoint {checkpoint_id!r} was not found for run {source_run_id!r}"
        )

    new_run_id = str(uuid4())
    diagnosis_graph.update_state(
        build_config(new_run_id),
        getattr(selected, "values", {}) or {},
        as_node=_checkpoint_predecessor(selected),
    )

    return new_run_id


def resume_from_checkpoint(
    run_id: str,
    checkpoint_id: str,
):
    return diagnosis_graph.invoke(
        None,
        config=build_config(
            run_id,
            checkpoint_id,
        ),
    )
