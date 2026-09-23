from __future__ import annotations

import re

from app.tools.ingestion.schemas import Chunk, Document


SENTENCE_RE = re.compile(r"[^.!?\u3002\uff01\uff1f\uff1b;]+[.!?\u3002\uff01\uff1f\uff1b;]?")


class RecursiveChunker:
    """Paragraph-first recursive splitter with sentence and hard-split fallbacks."""

    def __init__(self, chunk_size: int = 900):
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        self.chunk_size = chunk_size

    def chunk(self, document: Document) -> list[Chunk]:
        units: list[str] = []
        for paragraph in re.split(r"\n\s*\n", document.text):
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

        chunk_count = len(contents)
        return [
            Chunk(
                source=f"chunk_{index:04d}.md",
                title=document.source,
                content=content,
                chunk_index=index,
                chunk_count=chunk_count,
                source_id=f"recursive_chunk_{index:04d}",
            )
            for index, content in enumerate(contents, start=1)
        ]

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
