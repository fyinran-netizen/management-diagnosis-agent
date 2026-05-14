from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TextChunk:
    source: str
    title: str
    content: str
    chapter_title: str | None = None
    section_title: str | None = None
    chunk_index: int | None = None
    chunk_count: int | None = None


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines

    metadata: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return metadata, lines[index + 1 :]
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')

    return {}, lines


def parse_optional_int(value: str | None) -> int | None:
    if value is None or not value.isdigit():
        return None
    return int(value)


def split_markdown_by_headings(file_path: Path) -> list[TextChunk]:
    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    metadata, lines = parse_front_matter(text.splitlines())
    document_title = file_path.stem
    current_heading = document_title
    current_lines: list[str] = []
    chunks: list[TextChunk] = []

    chapter_title = metadata.get("chapter_title")
    section_title = metadata.get("section_title")
    chunk_index = parse_optional_int(metadata.get("chunk_index"))
    chunk_count = parse_optional_int(metadata.get("chunk_count"))

    def append_chunk() -> None:
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            return
        chunks.append(
            TextChunk(
                source=file_path.name,
                title=current_heading,
                content=content,
                chapter_title=chapter_title or document_title,
                section_title=section_title or current_heading,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            )
        )

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# "):
            document_title = stripped.replace("# ", "", 1).strip()
            chapter_title = chapter_title or document_title
            current_heading = document_title
            continue

        if stripped.startswith("## "):
            append_chunk()

            current_heading = stripped.replace("## ", "", 1).strip()
            section_title = section_title or current_heading
            current_lines = []
            continue

        current_lines.append(line)

    append_chunk()

    return [chunk for chunk in chunks if chunk.content]
