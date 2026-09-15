"""Raw-document evidence locations used by retrieval evaluation."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DOCUMENT = PROJECT_ROOT / "source_docs" / "raw_converted.md"
_CHAPTER_RE = re.compile(r"^# 第([一二三四五六七八九])章")
_SECTION_RE = re.compile(r"^## ")
_CHAPTER_DIGITS = "一二三四五六七八九"


def _paragraphs(lines: list[str]) -> list[str]:
    text = "\n".join(lines).strip()
    return [part.strip() for part in re.split(r"\r?\n\s*\r?\n", text) if part.strip()]


def load_raw_sections(path: Path = DEFAULT_RAW_DOCUMENT) -> dict[tuple[str, str], list[str]]:
    """Load section-local raw paragraphs, excluding headings and front matter/TOC."""
    sections: dict[tuple[str, str], list[str]] = {}
    chapter_id: str | None = None
    section_lines: list[str] | None = None
    section_number = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        chapter_match = _CHAPTER_RE.match(line)
        if chapter_match:
            if chapter_id and section_lines is not None:
                sections[(chapter_id, f"s{section_number:02d}")] = _paragraphs(section_lines)
            chapter_id = f"ch{_CHAPTER_DIGITS.index(chapter_match.group(1)) + 1:02d}"
            section_number = 0
            section_lines = None
            continue
        if chapter_id and _SECTION_RE.match(line):
            if section_lines is not None:
                sections[(chapter_id, f"s{section_number:02d}")] = _paragraphs(section_lines)
            section_number += 1
            section_lines = []
            continue
        if chapter_id and section_lines is not None:
            section_lines.append(line)
    if chapter_id and section_lines is not None:
        sections[(chapter_id, f"s{section_number:02d}")] = _paragraphs(section_lines)
    return sections


def resolve_expected_sources(
    expected_sources: list[dict[str, Any]],
    *,
    raw_sections: dict[tuple[str, str], list[str]] | None = None,
) -> list[str]:
    """Resolve inclusive-start/exclusive-end raw paragraph ranges to evidence text."""
    sections = raw_sections if raw_sections is not None else load_raw_sections()
    evidence: list[str] = []
    for index, location in enumerate(expected_sources):
        if set(location) != {"chapter_id", "section_id", "start", "end"}:
            raise ValueError(f"expected_sources[{index}] must contain only raw location fields")
        chapter_id = location["chapter_id"]
        section_id = location["section_id"]
        start = location["start"]
        end = location["end"]
        if not all(isinstance(value, str) for value in (chapter_id, section_id)):
            raise ValueError(f"expected_sources[{index}] chapter_id/section_id must be strings")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (start, end)):
            raise ValueError(f"expected_sources[{index}] start/end must be integers")
        paragraphs = sections.get((chapter_id, section_id))
        if paragraphs is None or not 0 <= start < end <= len(paragraphs):
            raise ValueError(f"expected_sources[{index}] does not resolve: {location}")
        evidence.append("\n\n".join(paragraphs[start:end]))
    return evidence


def load_cases(path: Path, *, expected_count: int | None = None) -> list[dict[str, Any]]:
    """Load cases and materialize raw ranges as runtime-only gold evidence."""
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        raise ValueError(f"Cases file must contain a JSON list of objects: {path}")
    if expected_count is not None and len(cases) != expected_count:
        raise ValueError(f"Expected {expected_count} retrieval cases, found {len(cases)} in {path}")
    raw_sections = load_raw_sections()
    for case in cases:
        case["gold_evidence"] = resolve_expected_sources(
            case["expected_sources"], raw_sections=raw_sections
        )
    return cases
