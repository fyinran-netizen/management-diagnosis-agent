from __future__ import annotations

import json
from typing import Any

from app.database.connection import get_diagnosis_connection
from app.database.schema import initialize_diagnosis_database


def save_diagnosis(record: dict[str, Any]) -> None:
    initialize_diagnosis_database()

    with get_diagnosis_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO diagnosis_records (
                project_id,
                created_at,
                company_context,
                goal,
                retrieved_sources,
                verification,
                revision_count,
                final_answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["project_id"],
                record["created_at"],
                record.get("company_context"),
                record.get("goal"),
                json.dumps(record.get("retrieved_sources", []), ensure_ascii=False),
                json.dumps(record.get("verification"), ensure_ascii=False),
                record.get("revision_count", 0),
                record.get("final_answer", ""),
            ),
        )