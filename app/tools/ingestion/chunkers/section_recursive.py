from __future__ import annotations

import re

from app.tools.ingestion.chunkers.section_based import SourceSection, parse_source_sections
from app.tools.ingestion.schemas import Chunk, Document


SENTENCE_RE = re.compile(r"[^.!?\u3002\uff01\uff1f\uff1b;]+[.!?\u3002\uff01\uff1f\uff1b;]?")


class SectionRecursiveChunker:
    """Recursively split each parsed section without crossing section boundaries."""

    def __init__(self, chunk_size: int = 900):
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        self.chunk_size = chunk_size

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
            if len(paragraph) <= self.chunk_size:
                units.append(paragraph)
            else:
                units.extend(self._split_sentences(paragraph))

        contents: list[str] = []
        current = ""
        for unit in units:
            candidate = f"{current}\n\n{unit}" if current else unit
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                contents.append(current)
                current = ""
            if len(unit) <= self.chunk_size:
                current = unit
            else:
                contents.extend(self._hard_split(unit))
        if current:
            contents.append(current)
        return contents

    def _split_sentences(self, paragraph: str) -> list[str]:
        sentences = [match.group(0).strip() for match in SENTENCE_RE.finditer(paragraph)]
        if not sentences:
            return self._hard_split(paragraph)
        parts: list[str] = []
        for sentence in sentences:
            if len(sentence) <= self.chunk_size:
                parts.append(sentence)
            else:
                parts.extend(self._hard_split(sentence))
        return parts

    def _hard_split(self, text: str) -> list[str]:
        return [
            text[start : start + self.chunk_size]
            for start in range(0, len(text), self.chunk_size)
        ]
