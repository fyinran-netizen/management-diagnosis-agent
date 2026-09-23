from __future__ import annotations

import re

import numpy as np

from app.tools.ingestion.chunkers.section_based import SourceSection, parse_source_sections
from app.tools.ingestion.schemas import Chunk, Document
from app.tools.retrieval.embeddings import embed_texts, get_embedding_model_name


SENTENCE_RE = re.compile(r"[^.!?\u3002\uff01\uff1f\uff1b;]+[.!?\u3002\uff01\uff1f\uff1b;]?")

# A sentence boundary is considered semantic when the normalized cosine
# similarity of adjacent sentences is <= this threshold. The threshold is
# intentionally explicit so later ablations can reproduce the same split.
DEFAULT_BREAKPOINT_SIMILARITY = 0.55
DEFAULT_MIN_CHARS = 300
DEFAULT_TARGET_CHARS = 900
DEFAULT_MAX_CHARS = 1200
SEMANTIC_START_CHARS = 600
TARGET_SELECTION_WINDOW_CHARS = 150


class SectionSemanticChunker:
    """Section-bounded semantic chunker with sentence-preserving packing."""

    def __init__(
        self,
        *,
        min_chars: int = DEFAULT_MIN_CHARS,
        target_chars: int = DEFAULT_TARGET_CHARS,
        max_chars: int = DEFAULT_MAX_CHARS,
        breakpoint_similarity: float = DEFAULT_BREAKPOINT_SIMILARITY,
        embedding_batch_size: int = 32,
    ):
        if not 1 <= min_chars <= target_chars <= max_chars:
            raise ValueError("expected 1 <= min_chars <= target_chars <= max_chars")
        if not -1.0 <= breakpoint_similarity <= 1.0:
            raise ValueError("breakpoint_similarity must be between -1 and 1")
        if embedding_batch_size < 1:
            raise ValueError("embedding_batch_size must be >= 1")
        self.min_chars = min_chars
        self.target_chars = target_chars
        self.max_chars = max_chars
        self.breakpoint_similarity = breakpoint_similarity
        self.embedding_batch_size = embedding_batch_size

    @classmethod
    def config(cls) -> dict[str, int | float | str | bool]:
        return {
            "embedding_model": get_embedding_model_name(),
            "sentence_splitter": "regex_terminal_punctuation",
            "min_chars": DEFAULT_MIN_CHARS,
            "target_chars": DEFAULT_TARGET_CHARS,
            "max_chars": DEFAULT_MAX_CHARS,
            "breakpoint_algorithm": "adjacent_sentence_cosine_similarity",
            "breakpoint_similarity_threshold": DEFAULT_BREAKPOINT_SIMILARITY,
            "breakpoint_rule": "choose the strongest eligible breakpoint near target; threshold gates candidates",
            "semantic_breakpoint_start_chars": SEMANTIC_START_CHARS,
            "target_selection_window_chars": TARGET_SELECTION_WINDOW_CHARS,
            "overlap_chars": 0,
            "cross_section": False,
        }

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
        sentence_units: list[str] = []
        body = "\n".join(section.body_lines)
        for paragraph in re.split(r"\n\s*\n", body):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            sentence_units.extend(self._split_sentences(paragraph))

        if not sentence_units:
            return []
        if len(sentence_units) == 1:
            return self._split_oversized_sentence(sentence_units[0])

        embeddings = embed_texts(sentence_units, batch_size=self.embedding_batch_size)
        chunks: list[str] = []
        start = 0
        while start < len(sentence_units):
            if len(sentence_units[start]) > self.max_chars:
                chunks.extend(self._split_oversized_sentence(sentence_units[start]))
                start += 1
                continue
            end = self._choose_boundary(start, sentence_units, embeddings)
            chunks.append("\n\n".join(sentence_units[start:end]))
            start = end

        # Avoid a tiny trailing chunk when it can be merged without exceeding
        # max_chars; otherwise preserve it because section boundaries are hard.
        if len(chunks) >= 2 and len(chunks[-1]) < self.min_chars:
            merged_length = len(chunks[-2]) + 2 + len(chunks[-1])
            if merged_length <= self.max_chars:
                chunks[-2] = f"{chunks[-2]}\n\n{chunks[-1]}"
                chunks.pop()
        return chunks

    def _choose_boundary(
        self,
        start: int,
        sentences: list[str],
        embeddings: np.ndarray,
    ) -> int:
        """Choose one sentence boundary using size-aware semantic scoring.

        No semantic boundary is eligible before 600 chars. Between 600 and
        1200 chars, threshold-passing boundaries compete using target-distance
        and semantic strength, with a 150-char target window preferred. If no
        semantic boundary is available, the nearest sentence boundary to the
        900-char target is used; max_chars is therefore a hard upper bound.
        """
        boundaries: list[tuple[int, int, float | None]] = []
        length = 0
        for end in range(start, len(sentences)):
            sentence_length = len(sentences[end])
            candidate_length = sentence_length if end == start else length + 2 + sentence_length
            if candidate_length > self.max_chars:
                break
            length = candidate_length
            boundary = end + 1
            similarity = (
                None
                if boundary == len(sentences)
                else float(np.dot(embeddings[boundary - 1], embeddings[boundary]))
            )
            boundaries.append((boundary, length, similarity))

        if not boundaries:
            return start + 1
        if boundaries[-1][0] == len(sentences):
            return len(sentences)

        eligible = [
            item
            for item in boundaries
            if item[1] >= SEMANTIC_START_CHARS
            and item[2] is not None
            and item[2] <= self.breakpoint_similarity
        ]
        target_window = [
            item
            for item in eligible
            if abs(item[1] - self.target_chars) <= TARGET_SELECTION_WINDOW_CHARS
        ]
        if target_window:
            # Within the target neighborhood, prefer the lowest similarity;
            # use distance to target only as a deterministic tie-breaker.
            return min(target_window, key=lambda item: (item[2], abs(item[1] - self.target_chars)))[0]
        if eligible:
            # Outside the neighborhood, semantic strength still matters, but
            # target distance is weighted enough to prevent early tiny chunks.
            return min(
                eligible,
                key=lambda item: (
                    abs(item[1] - self.target_chars) / self.target_chars
                    + 0.35 * float(item[2]),
                    abs(item[1] - self.target_chars),
                ),
            )[0]

        size_candidates = [item for item in boundaries if item[1] >= SEMANTIC_START_CHARS]
        if size_candidates:
            return min(size_candidates, key=lambda item: abs(item[1] - self.target_chars))[0]
        return boundaries[-1][0]

    @staticmethod
    def _split_sentences(paragraph: str) -> list[str]:
        sentences = [match.group(0).strip() for match in SENTENCE_RE.finditer(paragraph)]
        return [sentence for sentence in sentences if sentence] or [paragraph]

    def _split_oversized_sentence(self, sentence: str) -> list[str]:
        return [
            sentence[start : start + self.max_chars]
            for start in range(0, len(sentence), self.max_chars)
        ]
