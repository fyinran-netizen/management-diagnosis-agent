from __future__ import annotations

from collections.abc import Iterable

from app.tools.ingestion.schemas import Chunk, Metadata


class SourceMetadataBuilder:
    """Build deterministic source/chunk manifest records from chunks."""

    def build(self, chunks: Iterable[Chunk]) -> list[Metadata]:
        records: list[Metadata] = []
        for chunk in chunks:
            records.append(
                {
                    "source_id": chunk.source_id or self._source_id(chunk),
                    "path": chunk.source,
                    "chapter_id": chunk.chapter_id,
                    "section_id": chunk.section_id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_count": chunk.chunk_count,
                    "chapter_title": chunk.chapter_title,
                    "section_title": chunk.section_title,
                    "title": chunk.title,
                    "char_count": len(chunk.content),
                }
            )
        return records

    @staticmethod
    def _source_id(chunk: Chunk) -> str:
        path = chunk.source.removesuffix(".md").replace("/", "_")
        if "_chunk_" in path:
            return path
        index = chunk.chunk_index or 1
        return f"{path}_chunk_{index:02d}"
