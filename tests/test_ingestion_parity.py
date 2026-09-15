import json
from dataclasses import asdict
from pathlib import Path

from app.tools.ingestion.pipeline import ingest_knowledge_base
from app.tools.ingestion.repositories import FilesystemArtifactRepository


def test_ingestion_matches_preserved_chunk_artifact():
    result = ingest_knowledge_base(include_private=True, input_paths=[
        path for path in sorted((Path("data/private_knowledge_base")).glob("ch[0-9][0-9]/*.md"))
    ], persist=False)
    expected = json.loads(Path("data/vector_index/base/chunks.json").read_text(encoding="utf-8"))
    actual = [
        {
            key: value
            for key, value in asdict(chunk).items()
            if key not in {"source_id", "chapter_id", "section_id"}
        }
        for chunk in result.chunks
    ]
    assert len(actual) == len(expected)
    assert actual == expected


def test_ingestion_source_ids_match_preserved_index():
    index = FilesystemArtifactRepository(Path("data/private_knowledge_base")).load_source_metadata()
    by_path = {item["path"]: item for item in index if not item["path"].startswith("ch00/")}
    result = ingest_knowledge_base(include_private=True, input_paths=[
        path for path in sorted(Path("data/private_knowledge_base").glob("ch[0-9][0-9]/*.md"))
    ], persist=False)
    assert len(result.chunks) == len(by_path)
    for chunk in result.chunks:
        assert chunk.source_id == by_path[chunk.source]["source_id"]
