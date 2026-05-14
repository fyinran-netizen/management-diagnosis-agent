from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from app.rag.chunker import TextChunk


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_INDEX_DIR = PROJECT_ROOT / "data" / "vector_index"
CHUNKS_PATH = VECTOR_INDEX_DIR / "knowledge_chunks.json"
EMBEDDINGS_PATH = VECTOR_INDEX_DIR / "knowledge_embeddings.npy"
METADATA_PATH = VECTOR_INDEX_DIR / "index_metadata.json"


def chunk_to_embedding_text(chunk: TextChunk | dict[str, Any]) -> str:
    title = chunk.title if isinstance(chunk, TextChunk) else chunk.get("title", "")
    content = chunk.content if isinstance(chunk, TextChunk) else chunk.get("content", "")
    chapter_title = (
        chunk.chapter_title
        if isinstance(chunk, TextChunk)
        else chunk.get("chapter_title")
    )
    section_title = (
        chunk.section_title
        if isinstance(chunk, TextChunk)
        else chunk.get("section_title")
    )

    parts = [
        str(part).strip()
        for part in [chapter_title, section_title, title, content]
        if part
    ]
    return "\n".join(parts)


def save_vector_index(
    chunks: list[TextChunk],
    embeddings: np.ndarray,
    metadata: dict[str, Any],
    index_dir: Path = VECTOR_INDEX_DIR,
) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)

    chunk_dicts = [asdict(chunk) for chunk in chunks]
    (index_dir / CHUNKS_PATH.name).write_text(
        json.dumps(chunk_dicts, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    np.save(index_dir / EMBEDDINGS_PATH.name, embeddings)
    (index_dir / METADATA_PATH.name).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_vector_index(index_dir: Path = VECTOR_INDEX_DIR) -> tuple[list[dict[str, Any]], np.ndarray, dict[str, Any]]:
    chunks_path = index_dir / CHUNKS_PATH.name
    embeddings_path = index_dir / EMBEDDINGS_PATH.name
    metadata_path = index_dir / METADATA_PATH.name

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
