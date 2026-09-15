from __future__ import annotations

from pathlib import Path

from app.tools.ingestion.pipeline import ingest_knowledge_base
from app.tools.ingestion.schemas import IngestionResult


def ingest(
    *,
    include_private: bool = False,
    include_sample: bool = True,
    input_paths: list[Path] | None = None,
    persist: bool = True,
) -> IngestionResult:
    """Public ingestion boundary for application and graph callers."""
    return ingest_knowledge_base(
        include_private=include_private,
        include_sample=include_sample,
        input_paths=input_paths,
        persist=persist,
    )
