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


def evidence_matches(content: str, evidence: str) -> bool:
    """Exact normalized containment, including complete split sentence units."""
    content_norm = normalize_evidence(content)
    evidence_norm = normalize_evidence(evidence)
    if not content_norm or not evidence_norm:
        return False
    if evidence_norm in content_norm or content_norm in evidence_norm:
        return True
    return any(
        (unit_norm := normalize_evidence(unit))
        and (unit_norm in content_norm or content_norm in unit_norm)
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
