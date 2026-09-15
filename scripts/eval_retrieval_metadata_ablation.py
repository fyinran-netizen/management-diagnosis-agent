from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.retrievers.bm25 import (
    BM25_B,
    BM25_K1,
    SEMANTIC_METADATA_PATH,
    get_cached_bm25_index,
    retrieve_by_bm25,
)
from evaluation.retrieval.relevance import relevance_for
from evaluation.retrieval.evidence import load_cases as load_cases_with_evidence
from scripts.run_retrieval_benchmark import metrics_for

DEFAULT_CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_cases.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "tests" / "evals" / "reports" / "retrieval_metadata_ablation_report.json"

EXPERIMENTS = {
    "bm25_base": "base",
    "bm25_metadata_unweighted": "unweighted",
    "bm25_metadata_weighted": "weighted",
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    return load_cases_with_evidence(path)


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate_case(case: dict[str, Any], metadata_mode: str, top_k: int) -> dict[str, Any]:
    gold_evidence = [str(evidence) for evidence in case["gold_evidence"]]
    started = time.perf_counter()
    results = retrieve_by_bm25(case["query"], top_k=top_k, metadata_mode=metadata_mode)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    chunks = [
        {
            "source": str(item["source"]),
            "rank": rank,
            "bm25_score": float(item["bm25_score"]),
        }
        for rank, item in enumerate(results[:top_k], start=1)
    ]
    retrieved_sources = [chunk["source"] for chunk in chunks]
    relevant, covered_by_rank = relevance_for(results[:top_k], gold_evidence)
    metrics = metrics_for(relevant, covered_by_rank, len(gold_evidence), (3, 5))
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query": case["query"],
        "gold_evidence": gold_evidence,
        "retrieved_sources": retrieved_sources,
        **metrics,
        "retrieval_time_ms": elapsed_ms,
        "top_k_chunks": chunks,
    }


def summarize(cases: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "cases": float(len(cases)),
        "hit@3": average([case["hit@3"] for case in cases]),
        "hit@5": average([case["hit@5"] for case in cases]),
        "recall@5": average([case["recall@5"] for case in cases]),
        "mrr@5": average([case["mrr@5"] for case in cases]),
    }


def config(metadata_mode: str, top_k: int) -> dict[str, Any]:
    return {
        "top_k": top_k,
        "metadata_mode": metadata_mode,
        "metadata_path": str(SEMANTIC_METADATA_PATH),
        "bm25_k1": BM25_K1,
        "bm25_b": BM25_B,
        "tokenization": "tokenize_for_bm25",
        "document_structure": "chapter_title, section_title, title (twice), content",
        "metadata_fields": (
            []
            if metadata_mode == "base"
            else ["summary", "extracted.concept_keywords", "extracted.method_keywords", "extracted.named_entities", "inferred.symptom_keywords", "inferred.diagnosis_labels_zh", "inferred.diagnosis_tags", "inferred.recommended_methods"]
        ),
        "metadata_field_repetition": "none" if metadata_mode == "base" else ("once" if metadata_mode == "unweighted" else "current field weights"),
    }


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        try:
            os.replace(temp_name, path)
        except PermissionError:
            with path.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
            os.unlink(temp_name)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BM25 semantic metadata ablation.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")
    if not SEMANTIC_METADATA_PATH.exists():
        raise FileNotFoundError(f"Required semantic metadata file is missing: {SEMANTIC_METADATA_PATH}")

    cases = load_cases(args.cases)
    if len(cases) != 16:
        raise ValueError(f"Expected 16 retrieval cases, found {len(cases)}")

    # The mode is part of get_cached_bm25_index's cache key. Explicitly build
    # each mode here as an additional guard against accidental cache reuse.
    results: dict[str, Any] = {}
    for experiment_name, metadata_mode in EXPERIMENTS.items():
        get_cached_bm25_index.cache_clear()
        get_cached_bm25_index(metadata_mode)
        case_results = [evaluate_case(case, metadata_mode, args.top_k) for case in cases]
        results[experiment_name] = {
            "config": config(metadata_mode, args.top_k),
            "summary": summarize(case_results),
            "cases": case_results,
        }

    atomic_write(args.report, results)
    print("| experiment | hit@3 | hit@5 | recall@5 | mrr@5 |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for name, result in results.items():
        summary = result["summary"]
        print(f"| {name} | {summary['hit@3']:.3f} | {summary['hit@5']:.3f} | {summary['recall@5']:.3f} | {summary['mrr@5']:.3f} |")
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
