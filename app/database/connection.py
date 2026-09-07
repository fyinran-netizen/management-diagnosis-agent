from __future__ import annotations

import sqlite3

from app.core.config import DATABASE_DIR, DIAGNOSIS_DB_FILE


def get_diagnosis_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DIAGNOSIS_DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection