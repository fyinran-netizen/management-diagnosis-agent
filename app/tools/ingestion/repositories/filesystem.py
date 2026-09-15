from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import PRIVATE_KNOWLEDGE_DIR
from app.tools.ingestion.loaders.markdown import parse_front_matter
from app.tools.ingestion.schemas import Chunk, Metadata

_SOURCE_METADATA_FILE = "_index.json"
_SEMANTIC_METADATA_FILE = "semantic_metadata.jsonl"


class FilesystemArtifactRepository:
    """Filesystem adapter for the canonical private knowledge base."""

    def __init__(self, root: Path = PRIVATE_KNOWLEDGE_DIR):
        self.root = root

    def has_corpus(self) -> bool:
        return (self.root / _SOURCE_METADATA_FILE).exists()

    def load_source_metadata(self) -> list[Metadata]:
        value = self._read_json(_SOURCE_METADATA_FILE, [])
        return value if isinstance(value, list) else []

    def save_source_metadata(self, records: list[Metadata]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._write_json(self.root / _SOURCE_METADATA_FILE, records)

    def load_chunks(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for record in self.load_source_metadata():
            path_value = record.get("path")
            if not isinstance(path_value, str):
                continue
            path = self.root / path_value
            if not path.exists():
                continue
            chunks.append(self._read_chunk(path, record))
        return chunks

    def save_chunks(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            path = self.root / chunk.source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self._render_chunk(chunk), encoding="utf-8", newline="\n")

    def load_semantic_metadata(self) -> list[Metadata]:
        path = self.root / _SEMANTIC_METADATA_FILE
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def save_semantic_metadata(self, records: list[Metadata]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / _SEMANTIC_METADATA_FILE).write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _read_chunk(self, path: Path, record: Metadata) -> Chunk:
        front_matter, lines = parse_front_matter(path.read_text(encoding="utf-8").strip().splitlines())
        body: list[str] = []
        title = str(record.get("title") or path.stem)
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                continue
            if stripped.startswith("## "):
                continue
            body.append(line)
        metadata = {**front_matter, **record}
        return Chunk(
            source=str(record.get("path") or path.relative_to(self.root).as_posix()),
            title=title,
            content="\n".join(body).strip(),
            chapter_id=metadata.get("chapter_id"),
            section_id=metadata.get("section_id"),
            chapter_title=metadata.get("chapter_title"),
            section_title=metadata.get("section_title"),
            chunk_index=self._int(metadata.get("chunk_index")),
            chunk_count=self._int(metadata.get("chunk_count")),
            source_id=metadata.get("source_id"),
        )

    @staticmethod
    def _render_chunk(chunk: Chunk) -> str:
        lines = [
            "---",
            f"source_id: {chunk.source_id or ''}",
            f"chapter_id: {chunk.chapter_id or ''}",
            f"section_id: {chunk.section_id or ''}",
            f"chunk_index: {chunk.chunk_index or 1}",
            f"chunk_count: {chunk.chunk_count or 1}",
            f"chapter_title: {json.dumps(chunk.chapter_title or '', ensure_ascii=False)}",
            f"section_title: {json.dumps(chunk.section_title or '', ensure_ascii=False)}",
            f"title: {json.dumps(chunk.title, ensure_ascii=False)}",
            "---",
            "",
            f"# {chunk.chapter_title or chunk.title}",
        ]
        if chunk.section_title:
            lines.extend(["", f"## {chunk.section_title}"])
        lines.extend(["", chunk.content.strip(), ""])
        return "\n".join(lines)

    @staticmethod
    def _int(value: Any) -> int | None:
        return int(value) if isinstance(value, int) or (isinstance(value, str) and value.isdigit()) else None

    def _read_json(self, name: str, default: Any) -> Any:
        path = self.root / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
