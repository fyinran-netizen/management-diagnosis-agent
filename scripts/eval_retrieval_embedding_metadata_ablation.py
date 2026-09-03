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
from app.tools.retrieval.retrievers.embedding_metadata_retriever import (
    get_cached_vector_index_metadata,
    retrieve_by_embedding_metadata,
)
from app.tools.retrieval.retrievers.embedding_retriever import (
    get_cached_vector_index,
    retrieve_by_embedding,
)
from app.tools.retrieval.retrievers.hybrid_retriever import (
    CANDIDATE_MULTIPLIER,
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    MIN_CANDIDATES,
    normalize_scores,
    result_key,
    hybrid_retrieve,
)
from app.tools.retrieval.retrievers.keyword_retriever import retrieve_by_keyword
from app.tools.retrieval.retrievers.keyword_retriever import get_cached_bm25_index
from app.tools.retrieval.vector_store import (
    BASE_VECTOR_INDEX_DIR,
    SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
)

DEFAULT_CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_cases.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "tests" / "evals" / "reports" / "retrieval_embedding_metadata_ablation_report.json"

Retriever = Callable[[str, int], list[dict[str, Any]]]


def retrieve_linear_hybrid_metadata(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    candidate_k = max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES)
    keyword_results = retrieve_by_keyword(query, top_k=candidate_k)
    embedding_results = retrieve_by_embedding_metadata(query, top_k=candidate_k)

    normalize_scores(keyword_results, "keyword_score", "normalized_keyword_score")
    normalize_scores(embedding_results, "embedding_score", "normalized_embedding_score")
    for item in keyword_results:
        item["normalized_bm25_score"] = item.get("normalized_keyword_score", 0.0)
    for item in embedding_results:
        item["normalized_embedding_cosine_score"] = item.get(
            "normalized_embedding_score", 0.0
        )

    merged: dict[str, dict[str, Any]] = {}
    for item in keyword_results:
        merged[result_key(item)] = dict(item)
    for item in embedding_results:
        key = result_key(item)
        existing = merged.get(key)
        if existing is None:
            merged[key] = dict(item)
            continue
        existing.update(
            {
                "embedding_score": item.get("embedding_score"),
                "embedding_cosine_score": item.get("embedding_cosine_score"),
                "normalized_embedding_score": item.get("normalized_embedding_score"),
                "normalized_embedding_cosine_score": item.get(
                    "normalized_embedding_cosine_score"
                ),
            }
        )
        existing["retrieval_method"] = "hybrid"

    results: list[dict[str, Any]] = []
    for item in merged.values():
        keyword_score = float(item.get("normalized_keyword_score", 0.0))
        embedding_score = float(item.get("normalized_embedding_score", 0.0))
        final_score = KEYWORD_WEIGHT * keyword_score + EMBEDDING_WEIGHT * embedding_score
        item["hybrid_score"] = final_score
        item["score"] = final_score
        item.setdefault("bm25_score", item.get("keyword_score", 0.0))
        item.setdefault("embedding_cosine_score", item.get("embedding_score", 0.0))
        item.setdefault("normalized_bm25_score", item.get("normalized_keyword_score", 0.0))
        item.setdefault(
            "normalized_embedding_cosine_score",
            item.get("normalized_embedding_score", 0.0),
        )
        if item.get("retrieval_method") != "hybrid":
            item["retrieval_method"] = "hybrid"
        results.append(item)

    results.sort(key=lambda item: item["hybrid_score"], reverse=True)
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank
    return results[:top_k]


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError(f"Cases file must contain a JSON list: {path}")
    return cases


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
    expected_sources = list(dict.fromkeys(str(source) for source in case["expected_sources"]))
    expected = set(expected_sources)
    started = time.perf_counter()
    results = retriever(case["query"], top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    chunks = [diagnostics(item, method, rank) for rank, item in enumerate(results[:top_k], 1)]
    retrieved_sources = [item["source"] for item in chunks]
    top_3, top_5 = retrieved_sources[:3], retrieved_sources[:5]
    first_rank = next((rank for rank, source in enumerate(top_5, 1) if source in expected), 0)
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query": case["query"],
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "hit@3": 1.0 if any(source in expected for source in top_3) else 0.0,
        "hit@5": 1.0 if any(source in expected for source in top_5) else 0.0,
        "recall@5": len(set(source for source in top_5 if source in expected)) / len(expected) if expected else 0.0,
        "mrr@5": 1.0 / first_rank if first_rank else 0.0,
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
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")
    cases = load_cases(args.cases)
    if len(cases) != 16:
        raise ValueError(f"Expected 16 retrieval cases, found {len(cases)}")

    get_cached_vector_index.cache_clear()
    get_cached_vector_index_metadata.cache_clear()
    get_cached_bm25_index.cache_clear()

    experiments = {
        "base_embedding": (retrieve_by_embedding, "base_embedding", BASE_VECTOR_INDEX_DIR, False),
        "metadata_embedding": (retrieve_by_embedding_metadata, "metadata_embedding", SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR, False),
        "linear_hybrid_base": (hybrid_retrieve, "linear_hybrid", BASE_VECTOR_INDEX_DIR, True),
        "linear_hybrid_metadata": (retrieve_linear_hybrid_metadata, "linear_hybrid", SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR, True),
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
