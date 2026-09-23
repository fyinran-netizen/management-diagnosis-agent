"""Deterministic evidence matching for retrieval evaluation."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

SENTENCE_RE = re.compile(r"([^.!?\u3002\uff01\uff1f\uff1b;]+[.!?\u3002\uff01\uff1f\uff1b;]?)")


def normalize_evidence(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text)).lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalized)


def _content(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("content", ""))
    return str(getattr(item, "content", ""))


def _evidence_units(evidence: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", evidence) if part.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        sentences = [match.group(1).strip() for match in SENTENCE_RE.finditer(paragraph)]
        units.extend(sentence for sentence in sentences if sentence)
        if not sentences:
            units.append(paragraph)
    return units or [evidence]


def _find_occurrences(text: str, needle: str) -> list[int]:
    """Return all exact, possibly overlapping occurrence offsets."""
    if not needle:
        return []
    offsets: list[int] = []
    start = 0
    while (offset := text.find(needle, start)) >= 0:
        offsets.append(offset)
        start = offset + 1
    return offsets


def evidence_metrics_for(
    retrieved: Iterable[Any],
    gold_evidence: list[str],
    k: int,
) -> dict[str, float]:
    """Calculate normalized exact evidence coverage and density at rank k.

    Evidence coverage counts each normalized gold character position once, even
    when multiple retrieved chunks contain the same evidence text. Evidence
    density counts the matching normalized character positions in each retrieved
    chunk and divides by the normalized text length of the top-k chunks.
    """
    top_k = list(retrieved)[:k]
    content_norms = [normalize_evidence(_content(item)) for item in top_k]
    retrieved_chars = sum(len(content) for content in content_norms)
    gold_chars = 0
    covered_gold_chars = 0
    overlap_chars = 0

    for evidence in gold_evidence:
        evidence_norm = normalize_evidence(evidence)
        if not evidence_norm:
            continue
        gold_chars += len(evidence_norm)
        covered_positions: set[int] = set()
        content_positions = [set() for _ in content_norms]
        candidates = [evidence_norm]
        candidates.extend(
            unit_norm
            for unit in _evidence_units(evidence)
            if (unit_norm := normalize_evidence(unit)) and unit_norm != evidence_norm
        )
        for candidate in candidates:
            candidate_matched = False
            for content_index, content in enumerate(content_norms):
                for offset in _find_occurrences(content, candidate):
                    candidate_matched = True
                    content_positions[content_index].update(
                        range(offset, offset + len(candidate))
                    )
            if candidate_matched:
                for offset in _find_occurrences(evidence_norm, candidate):
                    covered_positions.update(range(offset, offset + len(candidate)))
        covered_gold_chars += len(covered_positions)
        overlap_chars += sum(len(positions) for positions in content_positions)

    return {
        "evidence_coverage": covered_gold_chars / gold_chars if gold_chars else 0.0,
        "evidence_density": overlap_chars / retrieved_chars if retrieved_chars else 0.0,
    }


def evidence_matches(content: str, evidence: str) -> bool:
    """Exact normalized containment, including complete split sentence units."""
    content_norm = normalize_evidence(content)
    evidence_norm = normalize_evidence(evidence)
    if not content_norm or not evidence_norm:
        return False
    if evidence_norm in content_norm:
        return True
    return any(
        (unit_norm := normalize_evidence(unit))
        and unit_norm in content_norm
        for unit in _evidence_units(evidence)
    )


def relevance_for(
    retrieved: Iterable[Any], gold_evidence: list[str]
) -> tuple[list[bool], list[set[int]]]:
    """Return per-rank relevance and cumulative covered evidence indices."""
    labels: list[bool] = []
    covered: set[int] = set()
    covered_by_rank: list[set[int]] = []
    for item in retrieved:
        matched = {
            index for index, evidence in enumerate(gold_evidence)
            if evidence_matches(_content(item), evidence)
        }
        covered.update(matched)
        labels.append(bool(matched))
        covered_by_rank.append(set(covered))
    return labels, covered_by_rank
