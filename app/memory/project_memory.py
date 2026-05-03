from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.agent.state import AgentState


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "data" / "project_memory"
MEMORY_FILE = MEMORY_DIR / "records.jsonl"


def save_project_record(state: AgentState) -> str:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

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
        "final_answer_preview": state.get("final_answer", "")[:500],
    }

    with MEMORY_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return project_id