from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.tools.ingestion.schemas import Chunk, Document

TARGET_CHARS = 900
MAX_CHARS = 1200
OVERLAP_CHARS = 180
SENTENCE_RE = re.compile(r"([^.!?。！？；;]+[.!?。！？；;]?)")
H1_RE = re.compile(r"^# (.+?)\s*$")
H2_RE = re.compile(r"^## (.+?)\s*$")
H3_RE = re.compile(r"^### (.+?)\s*$")
TOC_LINK_RE = re.compile(r"\[\d+\]\([^)]*\)\s*$")
DOT_LEADER_RE = re.compile(r".*\.{2,}\s*\d+\s*$")
CHAPTER_NUMBER_RE = re.compile(r"^\s*第([0-9一二三四五六七八九十百]+)章")
CHINESE_NUMBERS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


@dataclass
class SourceSection:
    chapter_id: str
    section_id: str
    chapter_title: str
    section_title: str
    body_lines: list[str]


def _is_toc_line(line: str) -> bool:
    stripped = line.strip()
    return bool(TOC_LINK_RE.search(stripped) or DOT_LEADER_RE.match(stripped))


def _chinese_number_to_int(value: str) -> int:
    if value.isdigit():
        return int(value)
    if value == "十":
        return 10
    if "十" in value:
        left, _, right = value.partition("十")
        return (CHINESE_NUMBERS.get(left, 1 if not left else 0) * 10) + CHINESE_NUMBERS.get(right, 0)
    return CHINESE_NUMBERS.get(value, 0)


def _chapter_id(title: str, fallback_index: int) -> str:
    match = CHAPTER_NUMBER_RE.match(title)
    if match:
        number = _chinese_number_to_int(match.group(1))
        if number:
            return f"ch{number:02d}"
    return "ch00" if fallback_index == 0 else f"ch{fallback_index:02d}"


def parse_source_sections(lines: list[str]) -> list[SourceSection]:
    """Parse the source Markdown using the historical chapter/section rules."""
    sections: list[SourceSection] = []
    chapter_title: str | None = None
    chapter_id: str | None = None
    chapter_index = 0
    section_index = 0
    section_title = ""
    body_lines: list[str] = []

    def flush(section_id_override: str | None = None) -> None:
        nonlocal body_lines
        if chapter_title is None or chapter_id is None:
            return
        trimmed = [line for line in body_lines]
        while trimmed and not trimmed[0].strip():
            trimmed.pop(0)
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        if not trimmed:
            return
        sections.append(SourceSection(
            chapter_id=chapter_id,
            section_id=section_id_override or f"s{max(section_index, 1):02d}",
            chapter_title=chapter_title,
            section_title=section_title,
            body_lines=trimmed,
        ))
        body_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if (match := H1_RE.match(line)):
            flush()
            chapter_title = match.group(1).strip()
            chapter_id = _chapter_id(chapter_title, chapter_index)
            chapter_index += 1
            section_index = 0
            section_title = ""
            body_lines = []
        elif (match := H2_RE.match(line)) and chapter_title is not None:
            flush("s00" if section_index == 0 and _paragraphs(body_lines) else None)
            section_index += 1
            section_title = match.group(1).strip()
            body_lines = []
        elif (match := H3_RE.match(line)) and chapter_title is not None:
            body_lines.extend(["", f"### {match.group(1).strip()}", ""])
        elif chapter_title is not None and not _is_toc_line(line):
            body_lines.append(line)
    flush()
    return sections


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
            previous = "\n\n".join(current).strip()
            chunks.append(previous)
            last = _paragraphs(previous.splitlines())[-1]
            overlap = last if len(last) <= OVERLAP_CHARS else last[-OVERLAP_CHARS:]
            current = [overlap, paragraph] if overlap else [paragraph]
            if len("\n\n".join(current).strip()) > MAX_CHARS:
                current = [paragraph]
        else:
            chunks.append(paragraph)
    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


class SectionBasedChunker:
    """Chapter/section split with bounded sections and paragraph overlap."""

    def chunk(self, document: Document) -> list[Chunk]:
        sections = parse_source_sections(document.text.splitlines())
        return chunk_source_sections(sections)


def chunk_source_sections(sections: list[SourceSection]) -> list[Chunk]:
    """Chunk raw source sections with the preserved legacy policy."""
    result: list[Chunk] = []
    for section in sections:
        texts = _split_body(section.body_lines)
        for index, text in enumerate(texts, start=1):
            filename = f"{section.section_id}.md"
            if len(texts) > 1:
                filename = f"{section.section_id}_chunk_{index:02d}.md"
            result.append(Chunk(
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
            ))
    return result
