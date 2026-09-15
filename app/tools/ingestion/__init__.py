"""Knowledge ingestion: load, chunk, enrich, and persist corpus artifacts."""

from app.tools.ingestion.pipeline import IngestionPipeline
from app.tools.ingestion.tool import ingest

__all__ = ["IngestionPipeline", "ingest"]
