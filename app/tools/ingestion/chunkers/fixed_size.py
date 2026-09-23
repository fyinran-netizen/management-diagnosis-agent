from __future__ import annotations

from app.tools.ingestion.schemas import Chunk, Document


class FixedSizeChunker:
    """Split the document's continuous text into non-overlapping fixed-size chunks."""

    def __init__(self, chunk_size: int):
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        self.chunk_size = chunk_size

    def chunk(self, document: Document) -> list[Chunk]:
        contents = [
            document.text[start : start + self.chunk_size]
            for start in range(0, len(document.text), self.chunk_size)
        ]
        chunk_count = len(contents)
        return [
            Chunk(
                source=f"chunk_{index:04d}.md",
                title=document.source,
                content=content,
                chunk_index=index,
                chunk_count=chunk_count,
                source_id=f"fixed_size_chunk_{index:04d}",
            )
            for index, content in enumerate(contents, start=1)
        ]
