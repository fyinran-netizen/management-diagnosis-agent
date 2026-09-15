from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.embeddings import get_embedding_model_name
from app.tools.retrieval.retrievers.embedding import (
    get_cached_vector_index,
    retrieve_by_embedding,
)
from app.tools.retrieval.retrievers.hybrid_linear import (
    CANDIDATE_MULTIPLIER,
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    MIN_CANDIDATES,
    hybrid_retrieve,
)
from app.tools.retrieval.retrievers.bm25 import retrieve_by_bm25 as retrieve_by_keyword
from app.tools.retrieval.retrievers.bm25 import get_cached_bm25_index
from app.tools.retrieval.vector_store import (
    BASE_VECTOR_INDEX_DIR,
    SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
)
from app.core.config import PRIVATE_KNOWLEDGE_DIR
from evaluation.retrieval.relevance import relevance_for
from evaluation.retrieval.evidence import load_cases as load_cases_with_evidence
from scripts.run_retrieval_benchmark import metrics_for

DEFAULT_CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_cases.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "tests" / "evals" / "reports" / "retrieval_embedding_metadata_ablation_report.json"

Retriever = Callable[[str, int], list[dict[str, Any]]]


def retrieve_linear_hybrid_metadata(
    query: str,
    top_k: int = 5,
    *,
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
) -> list[dict[str, Any]]:
    return hybrid_retrieve(
        query,
        top_k,
        corpus_dir=corpus_dir,
        embedding_index_dir=SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
        bm25_metadata_mode="unweighted",
    )


def load_cases(path: Path) -> list[dict[str, Any]]:
    return load_cases_with_evidence(path)


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def diagnostics(item: dict[str, Any], method: str, rank: int) -> dict[str, Any]:
    result = {
        "source": str(item.get("source", "")),
        "rank": rank,
        "retrieval_method": item.get("retrieval_method", method),
    }
    if method in {"base_embedding", "metadata_embedding"}:
        result["embedding_cosine_score"] = item.get(
            "embedding_cosine_score", item.get("embedding_score")
        )
    else:
        for key in (
            "bm25_score",
            "embedding_cosine_score",
            "normalized_bm25_score",
            "normalized_embedding_cosine_score",
            "hybrid_score",
        ):
            if key in item and item[key] is not None and number(item[key]) != 0:
                result[key] = item[key]
    return result


def evaluate_case(case: dict[str, Any], retriever: Retriever, method: str, top_k: int) -> dict[str, Any]:
    gold_evidence = [str(evidence) for evidence in case["gold_evidence"]]
    started = time.perf_counter()
    results = retriever(case["query"], top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    chunks = [diagnostics(item, method, rank) for rank, item in enumerate(results[:top_k], 1)]
    retrieved_sources = [item["source"] for item in chunks]
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


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(cases: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "cases": float(len(cases)),
        "hit@3": average([case["hit@3"] for case in cases]),
        "hit@5": average([case["hit@5"] for case in cases]),
        "recall@5": average([case["recall@5"] for case in cases]),
        "mrr@5": average([case["mrr@5"] for case in cases]),
        "average_retrieval_time_ms": average([case["retrieval_time_ms"] for case in cases]),
    }


def config(index_dir: Path, top_k: int, uses_hybrid: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "top_k": top_k,
        "embedding_model": get_embedding_model_name(),
        "index_dir": str(index_dir),
        "embedding_text": "chunk structure + unweighted semantic metadata" if "semantic_metadata" in str(index_dir) else "chunk structure",
    }
    if uses_hybrid:
        result.update(
            {
                "keyword_weight": KEYWORD_WEIGHT,
                "embedding_weight": EMBEDDING_WEIGHT,
                "candidate_multiplier": CANDIDATE_MULTIPLIER,
                "min_candidates": MIN_CANDIDATES,
                "candidate_k": max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES),
                "bm25_metadata_mode": "unweighted",
            }
        )
    return result


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
    parser = argparse.ArgumentParser(description="Evaluate base vs metadata embedding retrieval.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--corpus-dir", type=Path, default=PRIVATE_KNOWLEDGE_DIR)
    parser.add_argument("--index-dir", type=Path, default=BASE_VECTOR_INDEX_DIR)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")
    cases = load_cases(args.cases)
    if len(cases) != 16:
        raise ValueError(f"Expected 16 retrieval cases, found {len(cases)}")

    get_cached_vector_index.cache_clear()
    get_cached_bm25_index.cache_clear()

    experiments = {
        "base_embedding": (lambda query, top_k: retrieve_by_embedding(query, top_k, index_dir=args.index_dir), "base_embedding", args.index_dir, False),
        "metadata_embedding": (lambda query, top_k: retrieve_by_embedding(query, top_k, index_dir=SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR), "metadata_embedding", SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR, False),
        "linear_hybrid_base": (lambda query, top_k: hybrid_retrieve(query, top_k, corpus_dir=args.corpus_dir, embedding_index_dir=args.index_dir, bm25_metadata_mode="base"), "linear_hybrid", args.index_dir, True),
        "linear_hybrid_metadata": (lambda query, top_k: retrieve_linear_hybrid_metadata(query, top_k, corpus_dir=args.corpus_dir), "linear_hybrid", SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR, True),
    }
    report: dict[str, Any] = {}
    for name, (retriever, method, index_dir, uses_hybrid) in experiments.items():
        case_results = [evaluate_case(case, retriever, method, args.top_k) for case in cases]
        report[name] = {
            "config": config(index_dir, args.top_k, uses_hybrid),
            "summary": summarize(case_results),
            "cases": case_results,
        }
    atomic_write(args.report, report)

    print("| experiment | hit@3 | hit@5 | recall@5 | mrr@5 | avg ms |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name, result in report.items():
        summary = result["summary"]
        print(f"| {name} | {summary['hit@3']:.3f} | {summary['hit@5']:.3f} | {summary['recall@5']:.3f} | {summary['mrr@5']:.3f} | {summary['average_retrieval_time_ms']:.3f} |")
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
