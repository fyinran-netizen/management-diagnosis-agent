from __future__ import annotations

from app.database.connection import get_diagnosis_connection


def initialize_diagnosis_database() -> None:
    with get_diagnosis_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnosis_records (
                project_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                company_context TEXT,
                goal TEXT,
                retrieved_sources TEXT,
                verification TEXT,
                revision_count INTEGER NOT NULL DEFAULT 0,
                final_answer TEXT
            )
            """
        )