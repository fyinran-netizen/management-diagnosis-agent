from __future__ import annotations

from pathlib import Path

from app.rag.chunker import TextChunk, split_markdown_by_headings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "sample_knowledge_base"
PRIVATE_KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "private_knowledge_base"


def load_knowledge_base(include_private: bool = False) -> list[TextChunk]:
    chunks: list[TextChunk] = []

    if SAMPLE_KNOWLEDGE_DIR.exists():
        for path in sorted(SAMPLE_KNOWLEDGE_DIR.glob("*.md")):
            chunks.extend(split_markdown_by_headings(path))

    if include_private and PRIVATE_KNOWLEDGE_DIR.exists():
        for path in sorted(PRIVATE_KNOWLEDGE_DIR.glob("*.md")):
            chunks.extend(split_markdown_by_headings(path))

    return chunks