"""Reusable diagnostics for generated chunking experiment artifacts."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from app.tools.ingestion.repositories import FilesystemArtifactRepository


def _nearest_rank(values: list[int], percentile: float) -> int:
    """Return a deterministic nearest-rank percentile (1-based definition)."""
    return sorted(values)[max(0, math.ceil(percentile * len(values)) - 1)]


def _adjacent_overlap_length(left: str, right: str) -> int:
    """Return the longest exact suffix-prefix overlap between two contents."""
    max_length = min(len(left), len(right))
    for length in range(max_length, 0, -1):
        if left[-length:] == right[:length]:
            return length
    return 0


def calculate_overlap_diagnostics(contents: list[str]) -> tuple[int, int, float]:
    """Calculate exact adjacent overlap totals from final chunk contents."""
    total_chunk_chars = sum(len(content) for content in contents)
    total_overlap_chars = sum(
        _adjacent_overlap_length(left, right)
        for left, right in zip(contents, contents[1:])
    )
    overlap_ratio = (
        total_overlap_chars / total_chunk_chars if total_chunk_chars else 0.0
    )
    return total_chunk_chars, total_overlap_chars, overlap_ratio


def collect_chunking_diagnostics(
    corpus_dir: Path,
    *,
    embedding_index_build_time_ms: float,
    average_retrieval_time_ms: float,
) -> dict[str, Any]:
    """Calculate diagnostics from the generated corpus and benchmark timing."""
    chunks = FilesystemArtifactRepository(corpus_dir).load_chunks()
    lengths = [len(chunk.content) for chunk in chunks]
    if not lengths:
        raise ValueError(f"Experiment corpus contains no chunks: {corpus_dir}")
    total_chunk_chars, total_overlap_chars, overlap_ratio = calculate_overlap_diagnostics(
        [chunk.content for chunk in chunks]
    )
    return {
        "chunk_count": len(lengths),
        "mean_chunk_length": mean(lengths),
        "median_chunk_length": median(lengths),
        "p95_chunk_length": _nearest_rank(lengths, 0.95),
        "min_chunk_length": min(lengths),
        "max_chunk_length": max(lengths),
        "total_chunk_chars": total_chunk_chars,
        "total_overlap_chars": total_overlap_chars,
        "overlap_ratio": overlap_ratio,
        "embedding_index_build_time_ms": embedding_index_build_time_ms,
        "average_retrieval_time_ms": average_retrieval_time_ms,
    }


def append_diagnostics_markdown(markdown: str, diagnostics: dict[str, Any]) -> str:
    """Append the standard chunking diagnostics section to a benchmark report."""
    def value(key: str, digits: int = 2) -> str:
        raw = diagnostics[key]
        return "N/A" if raw is None else f"{raw:.{digits}f}" if isinstance(raw, float) else str(raw)

    section = "\n\n## Chunking diagnostics\n\n"
    section += "| Metric | Value |\n| --- | ---: |\n"
    section += f"| Chunk count | {value('chunk_count')} |\n"
    section += f"| Mean length | {value('mean_chunk_length')} |\n"
    section += f"| Median length | {value('median_chunk_length')} |\n"
    section += f"| P95 length | {value('p95_chunk_length')} |\n"
    section += f"| Min length | {value('min_chunk_length')} |\n"
    section += f"| Max length | {value('max_chunk_length')} |\n"
    section += f"| Total chunk chars | {value('total_chunk_chars')} |\n"
    section += f"| Total overlap chars | {value('total_overlap_chars')} |\n"
    section += f"| Overlap ratio | {value('overlap_ratio', digits=4)} |\n"
    section += f"| Embedding index build time (ms) | {value('embedding_index_build_time_ms')} |\n"
    section += f"| Average retrieval latency (ms) | {value('average_retrieval_time_ms')} |\n"
    return markdown.rstrip() + section


def append_experiment_log(
    path: Path,
    *,
    strategy: str,
    report_path: Path,
    markdown_path: Path,
    diagnostics: dict[str, Any],
) -> None:
    """Record strategy-level diagnostics alongside the existing experiment log."""
    record = {
        "experiment": "chunking_experiment_v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "report": str(report_path),
        "markdown_report": str(markdown_path),
        "chunking_diagnostics": diagnostics,
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
