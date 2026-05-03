from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TextChunk:
    source: str
    title: str
    content: str


def split_markdown_by_headings(file_path: Path) -> list[TextChunk]:
    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    lines = text.splitlines()
    document_title = file_path.stem
    current_heading = document_title
    current_lines: list[str] = []
    chunks: list[TextChunk] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# "):
            document_title = stripped.replace("# ", "", 1).strip()
            current_heading = document_title
            continue

        if stripped.startswith("## "):
            if current_lines:
                chunks.append(
                    TextChunk(
                        source=file_path.name,
                        title=current_heading,
                        content="\n".join(current_lines).strip(),
                    )
                )

            current_heading = stripped.replace("## ", "", 1).strip()
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        chunks.append(
            TextChunk(
                source=file_path.name,
                title=current_heading,
                content="\n".join(current_lines).strip(),
            )
        )

    return [chunk for chunk in chunks if chunk.content]