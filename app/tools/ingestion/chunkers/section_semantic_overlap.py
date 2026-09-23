from __future__ import annotations

from app.tools.ingestion.chunkers.section_based import SourceSection
from app.tools.ingestion.chunkers.section_semantic import SectionSemanticChunker


DEFAULT_OVERLAP_CHARS = 180


class SectionSemanticOverlapChunker(SectionSemanticChunker):
    """Current section-semantic splitter with sentence-preserving overlap."""

    def __init__(self, *, overlap_chars: int = DEFAULT_OVERLAP_CHARS, **kwargs):
        if overlap_chars < 1:
            raise ValueError("overlap_chars must be >= 1")
        super().__init__(**kwargs)
        self.overlap_chars = overlap_chars

    @classmethod
    def config(cls) -> dict[str, int | float | str | bool]:
        config = super().config()
        config.update(
            {
                "overlap_chars": DEFAULT_OVERLAP_CHARS,
                "overlap_policy": "suffix of complete sentences; approximate length allowed",
            }
        )
        return config

    def _split_section(self, section: SourceSection) -> list[str]:
        # The parent produces the exact latest zero-overlap size-aware semantic
        # chunks. Only the inter-chunk context is added here, per section.
        base_chunks = super()._split_section(section)
        if len(base_chunks) < 2:
            return base_chunks

        chunks = [base_chunks[0]]
        for content in base_chunks[1:]:
            overlap = self._sentence_suffix(chunks[-1])
            chunks.append(f"{overlap}\n\n{content}" if overlap else content)
        return chunks

    def _sentence_suffix(self, content: str) -> str:
        sentences = self._split_sentences(content)
        selected: list[str] = []
        length = 0
        for sentence in reversed(sentences):
            candidate_length = len(sentence) if not selected else length + 2 + len(sentence)
            if selected and candidate_length > self.overlap_chars:
                break
            selected.insert(0, sentence)
            length = candidate_length
            # If one complete sentence is longer than the requested overlap,
            # retain it intact rather than cutting through its middle.
            if length >= self.overlap_chars:
                break
        return "\n\n".join(selected)
