from __future__ import annotations

from app.tools.ingestion.chunkers.section_based import SourceSection, parse_source_sections
from app.tools.ingestion.schemas import Chunk, Document


class SectionRawChunker:
    """Chapter/section split that keeps each parsed section as one chunk."""

    def chunk(self, document: Document) -> list[Chunk]:
        sections = parse_source_sections(document.text.splitlines())
        return chunk_raw_source_sections(sections)


def chunk_raw_source_sections(sections: list[SourceSection]) -> list[Chunk]:
    """Create one metadata-preserving chunk for each raw parsed section."""
    return [
        Chunk(
            source=f"{section.chapter_id}/{section.section_id}.md",
            title=section.section_title or section.chapter_title,
            content="\n".join(section.body_lines),
            chapter_id=section.chapter_id,
            section_id=section.section_id,
            chapter_title=section.chapter_title,
            section_title=section.section_title,
            chunk_index=1,
            chunk_count=1,
            source_id=f"{section.chapter_id}_{section.section_id}_chunk_01",
        )
        for section in sections
    ]
