from __future__ import annotations

import re

from app.tools.ingestion.chunkers.section_based import SourceSection, parse_source_sections
from app.tools.ingestion.schemas import Chunk, Document


CHUNK_SIZE = 900
OVERLAP_CHARS = 180
SENTENCE_RE = re.compile(r"[^.!?。！？；;]+[.!?。！？；;]?")


class SectionRecursiveOverlapChunker:
    """Independent section-recursive baseline with 180-character overlap."""

    def chunk(self, document: Document) -> list[Chunk]:
        sections = parse_source_sections(document.text.splitlines())
        result: list[Chunk] = []
        for section in sections:
            contents = self._split_section(section)
            for index, content in enumerate(contents, start=1):
                filename = f"{section.section_id}.md"
                if len(contents) > 1:
                    filename = f"{section.section_id}_chunk_{index:02d}.md"
                result.append(
                    Chunk(
                        source=f"{section.chapter_id}/{filename}",
                        title=section.section_title or section.chapter_title,
                        content=content,
                        chapter_id=section.chapter_id,
                        section_id=section.section_id,
                        chapter_title=section.chapter_title,
                        section_title=section.section_title,
                        chunk_index=index,
                        chunk_count=len(contents),
                        source_id=f"{section.chapter_id}_{section.section_id}_chunk_{index:02d}",
                    )
                )
        return result

    def _split_section(self, section: SourceSection) -> list[str]:
        units: list[str] = []
        body = "\n".join(section.body_lines)
        for paragraph in re.split(r"\n\s*\n", body):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(paragraph) <= CHUNK_SIZE:
                units.append(paragraph)
            else:
                units.extend(self._split_sentences(paragraph))

        base_chunks: list[str] = []
        current = ""
        for unit in units:
            candidate = f"{current}\n\n{unit}" if current else unit
            if len(candidate) <= CHUNK_SIZE:
                current = candidate
                continue
            if current:
                base_chunks.append(current)
                current = ""
            if len(unit) <= CHUNK_SIZE:
                current = unit
            else:
                base_chunks.extend(self._hard_split(unit))
        if current:
            base_chunks.append(current)

        if not base_chunks:
            return []
        contents = [base_chunks[0]]
        for chunk in base_chunks[1:]:
            contents.append(f"{contents[-1][-OVERLAP_CHARS:]}\n\n{chunk}")
        return contents

    def _split_sentences(self, paragraph: str) -> list[str]:
        sentences = [match.group(0).strip() for match in SENTENCE_RE.finditer(paragraph)]
        if not sentences:
            return self._hard_split(paragraph)
        parts: list[str] = []
        for sentence in sentences:
            if len(sentence) <= CHUNK_SIZE:
                parts.append(sentence)
            else:
                parts.extend(self._hard_split(sentence))
        return parts

    def _hard_split(self, text: str) -> list[str]:
        return [text[start : start + CHUNK_SIZE] for start in range(0, len(text), CHUNK_SIZE)]
