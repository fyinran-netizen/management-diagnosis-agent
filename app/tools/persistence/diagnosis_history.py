from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.agent.state import AgentState
from app.database.diagnosis_repository import save_diagnosis


def save_diagnosis_record(state: AgentState) -> str:
    project_id = state.get("project_id") or str(uuid4())

    record = {
        "project_id": project_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "company_context": state.get("company_context"),
        "goal": state.get("goal"),
        "retrieved_sources": [
            {
                "source": item.get("source"),
                "title": item.get("title"),
                "score": item.get("score"),
            }
            for item in state.get("retrieved_chunks", [])
        ],
        "verification": state.get("verification"),
        "revision_count": state.get("revision_count", 0),
        "final_answer": state.get("final_answer", ""),
    }

    save_diagnosis(record)
    return project_id