from __future__ import annotations

import re
from typing import Iterable

from app.tools.ingestion.chunkers.section_based import (
    SourceSection,
    parse_source_sections,
)
from app.tools.ingestion.schemas import Chunk, Document


TARGET_CHARS = 900
MAX_CHARS = 1200
OVERLAP_CHARS = 0
SENTENCE_RE = re.compile(r"([^.!?。！？，；;]+[.!?。！？，；;]?)")


def _paragraphs(lines: Iterable[str]) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            result.append("\n".join(current).strip())
            current = []
    if current:
        result.append("\n".join(current).strip())
    return result


def _split_long_text(text: str) -> list[str]:
    sentences = [m.group(1).strip() for m in SENTENCE_RE.finditer(text)] or [text]
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        candidate = f"{current}{sentence}" if current else sentence
        if len(candidate) <= MAX_CHARS:
            current = candidate
        else:
            if current:
                pieces.append(current)
            if len(sentence) <= MAX_CHARS:
                current = sentence
            else:
                pieces.extend(sentence[i : i + MAX_CHARS] for i in range(0, len(sentence), MAX_CHARS))
                current = ""
    if current:
        pieces.append(current)
    return pieces


def _split_body(lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in _paragraphs(lines):
        paragraphs.extend([paragraph] if len(paragraph) <= MAX_CHARS else _split_long_text(paragraph))
    chunks: list[str] = []
    current: list[str] = []
    for paragraph in paragraphs:
        candidate = "\n\n".join(current + [paragraph]).strip()
        if len(candidate) <= MAX_CHARS and (len(candidate) <= TARGET_CHARS or not current):
            current.append(paragraph)
            continue
        if current:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
        else:
            chunks.append(paragraph)
    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


class SectionBasedNoOverlapChunker:
    """Independent section-based baseline with the legacy overlap disabled."""

    def chunk(self, document: Document) -> list[Chunk]:
        sections = parse_source_sections(document.text.splitlines())
        result: list[Chunk] = []
        for section in sections:
            texts = _split_body(section.body_lines)
            for index, text in enumerate(texts, start=1):
                filename = f"{section.section_id}.md"
                if len(texts) > 1:
                    filename = f"{section.section_id}_chunk_{index:02d}.md"
                result.append(
                    Chunk(
                        source=f"{section.chapter_id}/{filename}",
                        title=section.section_title or section.chapter_title,
                        content=text,
                        chapter_id=section.chapter_id,
                        section_id=section.section_id,
                        chapter_title=section.chapter_title,
                        section_title=section.section_title,
                        chunk_index=index,
                        chunk_count=len(texts),
                        source_id=f"{section.chapter_id}_{section.section_id}_chunk_{index:02d}",
                    )
                )
        return result
