from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from app.tools.ingestion.schemas import Chunk


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTOR_INDEX_ROOT = PROJECT_ROOT / "data" / "vector_index"
BASE_VECTOR_INDEX_DIR = VECTOR_INDEX_ROOT / "base"
SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR = VECTOR_INDEX_ROOT / "semantic_metadata_unweighted"
# Production retrieval keeps its existing API and now reads the preserved base index.
VECTOR_INDEX_DIR = BASE_VECTOR_INDEX_DIR
CHUNKS_PATH = VECTOR_INDEX_DIR / "chunks.json"
EMBEDDINGS_PATH = VECTOR_INDEX_DIR / "embeddings.npy"
METADATA_PATH = VECTOR_INDEX_DIR / "manifest.json"
LEGACY_INDEX_FILENAMES = (
    "knowledge_chunks.json",
    "knowledge_embeddings.npy",
    "index_metadata.json",
)


def _index_filenames(index_dir: Path) -> tuple[str, str, str]:
    if index_dir == SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR:
        return LEGACY_INDEX_FILENAMES
    return CHUNKS_PATH.name, EMBEDDINGS_PATH.name, METADATA_PATH.name


def chunk_to_embedding_text(chunk: Chunk | dict[str, Any]) -> str:
    title = chunk.title if isinstance(chunk, Chunk) else chunk.get("title", "")
    content = chunk.content if isinstance(chunk, Chunk) else chunk.get("content", "")
    chapter_title = (
        chunk.chapter_title
        if isinstance(chunk, Chunk)
        else chunk.get("chapter_title")
    )
    section_title = (
        chunk.section_title
        if isinstance(chunk, Chunk)
        else chunk.get("section_title")
    )

    parts = [
        str(part).strip()
        for part in [chapter_title, section_title, title, content]
        if part
    ]
    return "\n".join(parts)


def save_vector_index(
    chunks: list[Chunk],
    embeddings: np.ndarray,
    metadata: dict[str, Any],
    index_dir: Path = VECTOR_INDEX_DIR,
) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)

    chunk_dicts = [
        {key: value for key, value in asdict(chunk).items() if key != "source_id"}
        for chunk in chunks
    ]
    chunks_name, embeddings_name, metadata_name = _index_filenames(index_dir)
    (index_dir / chunks_name).write_text(json.dumps(chunk_dicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    np.save(index_dir / embeddings_name, embeddings)
    (index_dir / metadata_name).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_vector_index(index_dir: Path = VECTOR_INDEX_DIR) -> tuple[list[dict[str, Any]], np.ndarray, dict[str, Any]]:
    chunks_name, embeddings_name, metadata_name = _index_filenames(index_dir)
    chunks_path = index_dir / chunks_name
    embeddings_path = index_dir / embeddings_name
    metadata_path = index_dir / metadata_name

    if not chunks_path.exists() or not embeddings_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            "Vector index is missing. Run `uv run python scripts/build_vector_index.py` first."
        )

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    embeddings = np.load(embeddings_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    if len(chunks) != embeddings.shape[0]:
        raise ValueError(
            f"Vector index is inconsistent: {len(chunks)} chunks but {embeddings.shape[0]} embeddings."
        )

    return chunks, embeddings, metadata
