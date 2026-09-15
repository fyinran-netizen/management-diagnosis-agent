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

from app.tools.retrieval.retrievers.embedding import retrieve_by_embedding
from app.tools.retrieval.embeddings import get_embedding_model_name
from app.tools.retrieval.retrievers.bm25 import (
    SEMANTIC_METADATA_PATH,
    get_cached_bm25_index,
    load_semantic_metadata_by_source,
    load_semantic_metadata_by_source_unweighted,
)
from app.tools.retrieval.retrievers.embedding import get_cached_vector_index
from app.tools.retrieval.retrievers.hybrid_linear import (
    CANDIDATE_MULTIPLIER,
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    MIN_CANDIDATES,
    hybrid_retrieve,
)
from app.tools.retrieval.retrievers.hybrid_rrf import (
    RRF_CANDIDATE_MULTIPLIER,
    RRF_K,
    RRF_MIN_CANDIDATES,
    hybrid_retrieve_rrf,
)
from app.tools.retrieval.retrievers.bm25 import retrieve_by_bm25
from evaluation.retrieval.relevance import relevance_for
from evaluation.retrieval.evidence import load_cases as load_cases_with_evidence
from scripts.run_retrieval_benchmark import metrics_for

DEFAULT_CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_cases.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "tests" / "evals" / "reports" / "retrieval_eval_report.json"
DEFAULT_LEGACY_REPORT_PATH = PROJECT_ROOT / "tests" / "evals" / "reports" / "retrieval_eval_report_weighted_metadata.json"
Retriever = Callable[[str, int], list[dict[str, Any]]]

STRATEGIES: dict[str, Retriever] = {
    "embedding": retrieve_by_embedding,
    "bm25": retrieve_by_bm25,
    "linear_hybrid": hybrid_retrieve,
    "rrf_hybrid": hybrid_retrieve_rrf,
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    return load_cases_with_evidence(path)


def load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError(f"Report file must contain a JSON object: {path}")
    return report


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def annotate_chunks(results: list[dict[str, Any]], method: str, top_k: int) -> list[dict[str, Any]]:
    selected = results[:top_k]
    chunks: list[dict[str, Any]] = []
    for rank, item in enumerate(selected, start=1):
        chunk: dict[str, Any] = {
            "source": str(item.get("source", "")),
            "rank": rank,
            "retrieval_method": item.get("retrieval_method", method),
        }
        if method == "embedding":
            chunk["embedding_score"] = item.get("embedding_cosine_score", item.get("embedding_score"))
        elif method == "bm25":
            chunk["bm25_score"] = item.get("bm25_score", item.get("keyword_score"))
        elif method == "linear_hybrid":
            for key in (
                "bm25_score",
                "embedding_cosine_score",
                "normalized_bm25_score",
                "normalized_embedding_cosine_score",
                "hybrid_score",
            ):
                if key in item and item[key] is not None and number(item[key]) != 0:
                    chunk[key] = item[key]
        elif method == "rrf_hybrid":
            for key in (
                "bm25_score",
                "embedding_cosine_score",
                "keyword_rank",
                "embedding_rank",
                "rrf_score",
            ):
                if key in item and item[key] is not None and (
                    key.endswith("_rank") or number(item[key]) != 0
                ):
                    chunk[key] = item[key]
        chunks.append(chunk)
    return chunks


def evaluate_case(case: dict[str, Any], retriever: Retriever, method: str, top_k: int) -> dict[str, Any]:
    gold_evidence = [str(evidence) for evidence in case["gold_evidence"]]
    started = time.perf_counter()
    results = retriever(str(case["query"]), top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    chunks = annotate_chunks(results, method, top_k)
    retrieved_sources = [chunk["source"] for chunk in chunks]
    relevant, covered_by_rank = relevance_for(results[:top_k], gold_evidence)
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query": case["query"],
        "gold_evidence": gold_evidence,
        "retrieved_sources": retrieved_sources,
        **metrics_for(relevant, covered_by_rank, len(gold_evidence), (3, 5)),
        "retrieval_time_ms": elapsed_ms,
        "top_k_chunks": chunks,
    }


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(cases: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "cases": float(len(cases)),
        "hit@3": average([number(case["hit@3"]) for case in cases]),
        "hit@5": average([number(case["hit@5"]) for case in cases]),
        "recall@5": average([number(case["recall@5"]) for case in cases]),
        "mrr@5": average([number(case["mrr@5"]) for case in cases]),
        "average_retrieval_time_ms": average([number(case["retrieval_time_ms"]) for case in cases]),
    }


def strategy_config(method: str, top_k: int) -> dict[str, Any]:
    config: dict[str, Any] = {"top_k": top_k}
    if method in {"embedding", "linear_hybrid", "rrf_hybrid"}:
        config["embedding_model"] = get_embedding_model_name()
    if method in {"bm25", "linear_hybrid", "rrf_hybrid"}:
        config["bm25_metadata_mode"] = "unweighted"
        config["bm25_metadata_path"] = str(SEMANTIC_METADATA_PATH)
    if method == "linear_hybrid":
        config.update(
            {
                "keyword_weight": KEYWORD_WEIGHT,
                "embedding_weight": EMBEDDING_WEIGHT,
                "candidate_multiplier": CANDIDATE_MULTIPLIER,
                "min_candidates": MIN_CANDIDATES,
                "candidate_k": max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES),
            }
        )
    elif method == "rrf_hybrid":
        config.update(
            {
                "rrf_k": RRF_K,
                "candidate_multiplier": RRF_CANDIDATE_MULTIPLIER,
                "min_candidates": RRF_MIN_CANDIDATES,
                "candidate_k": max(top_k * RRF_CANDIDATE_MULTIPLIER, RRF_MIN_CANDIDATES),
            }
        )
    return config


def evaluate_strategy(method: str, retriever: Retriever, cases: list[dict[str, Any]], top_k: int) -> dict[str, Any]:
    case_results = [evaluate_case(case, retriever, method, top_k) for case in cases]
    return {"config": strategy_config(method, top_k), "summary": summarize(case_results), "cases": case_results}


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        try:
            os.replace(temporary_name, path)
        except PermissionError:
            # Some Windows workspace ACLs allow modifying an existing file but
            # deny deleting/replacing it. All evaluation work is complete at
            # this point, so safely fall back to an in-place overwrite.
            with path.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.unlink(temporary_name)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the four current retrieval strategies directly.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")

    cases = load_cases(args.cases)
    if len(cases) != 16:
        raise ValueError(f"Expected 16 retrieval cases, found {len(cases)} in {args.cases}")
    source_report_path = args.report if args.report.exists() else DEFAULT_LEGACY_REPORT_PATH
    report = load_report(source_report_path)

    # Clear retrieval indexes before this run so no previous BM25 mode is reused.
    get_cached_bm25_index.cache_clear()
    load_semantic_metadata_by_source.cache_clear()
    load_semantic_metadata_by_source_unweighted.cache_clear()
    get_cached_vector_index.cache_clear()

    # Run all strategies before touching the report, so failures leave it unchanged.
    new_results = {
        method: evaluate_strategy(method, retriever, cases, args.top_k)
        for method, retriever in STRATEGIES.items()
    }
    if "keyword" not in report:
        raise ValueError(f"Legacy report must contain the keyword result: {source_report_path}")
    # Deliberately construct a fresh top-level object: legacy keyword is kept
    # verbatim, while obsolete historical strategy keys are dropped.
    updated_report = {"keyword": report["keyword"], **new_results}
    atomic_write_json(args.report, updated_report)

    print("| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 | avg retrieval ms |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for method, result in new_results.items():
        summary = result["summary"]
        print(
            f"| {method} | {int(summary['cases'])} | {summary['hit@3']:.3f} | "
            f"{summary['hit@5']:.3f} | {summary['recall@5']:.3f} | "
            f"{summary['mrr@5']:.3f} | {summary['average_retrieval_time_ms']:.3f} |"
        )
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
