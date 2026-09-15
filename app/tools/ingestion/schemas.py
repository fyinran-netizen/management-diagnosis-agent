from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias

Metadata: TypeAlias = dict[str, Any]


@dataclass
class Document:
    source: str
    text: str
    metadata: Metadata = field(default_factory=dict)


@dataclass
class Chunk:
    source: str
    title: str
    content: str
    chapter_id: str | None = None
    section_id: str | None = None
    chapter_title: str | None = None
    section_title: str | None = None
    chunk_index: int | None = None
    chunk_count: int | None = None
    source_id: str | None = None


@dataclass
class IngestionResult:
    documents: list[Document] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    source_metadata: list[Metadata] = field(default_factory=list)
    semantic_metadata: list[Metadata] = field(default_factory=list)
    skipped: bool = False
    reason: str | None = None
