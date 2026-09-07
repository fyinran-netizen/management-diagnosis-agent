from __future__ import annotations

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

from app.core.config import CHECKPOINT_DB_FILE, DATABASE_DIR


DATABASE_DIR.mkdir(parents=True, exist_ok=True)

_connection = sqlite3.connect(
    CHECKPOINT_DB_FILE,
    check_same_thread=False,
)

checkpoint_saver = SqliteSaver(_connection)