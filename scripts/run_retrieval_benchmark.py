from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.retrievers.bm25 import (  # noqa: E402
    PRODUCTION_BM25_METADATA_MODE,
    clear_bm25_caches,
    retrieve_by_bm25,
)
from app.tools.retrieval.retrievers.embedding import (  # noqa: E402
    get_cached_vector_index,
    retrieve_by_embedding,
)
from app.tools.retrieval.retrievers.hybrid_linear import hybrid_retrieve  # noqa: E402
from app.tools.retrieval.retrievers.hybrid_linear import (  # noqa: E402
    CANDIDATE_MULTIPLIER,
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    MIN_CANDIDATES,
)
from app.tools.retrieval.retrievers.hybrid_rrf import (  # noqa: E402
    RRF_CANDIDATE_MULTIPLIER,
    RRF_K,
    RRF_MIN_CANDIDATES,
    hybrid_retrieve_rrf,
)
from app.tools.retrieval.retrievers.keyword import (  # noqa: E402
    retrieve_by_keyword as retrieve_by_keyword_baseline,
)
from app.tools.retrieval.vector_store import (  # noqa: E402
    BASE_VECTOR_INDEX_DIR,
    SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
)
from app.tools.retrieval.embeddings import get_embedding_model_name  # noqa: E402


DEFAULT_CASES = PROJECT_ROOT / "evaluation" / "retrieval" / "cases" / "retrieval_cases.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "evaluation" / "retrieval" / "reports"
DEFAULT_EXPERIMENTS = PROJECT_ROOT / "evaluation" / "retrieval" / "experiments.jsonl"
DEFAULT_KS = (1, 3, 5, 10, 20)

Retriever = Callable[[str, int], list[dict[str, Any]]]


def retrieve_bm25_base(query: str, top_k: int) -> list[dict[str, Any]]:
    return retrieve_by_bm25(query, top_k=top_k, metadata_mode="base")


def retrieve_bm25_metadata(query: str, top_k: int) -> list[dict[str, Any]]:
    return retrieve_by_bm25(query, top_k=top_k, metadata_mode="unweighted")


def retrieve_metadata_embedding(query: str, top_k: int) -> list[dict[str, Any]]:
    return retrieve_by_embedding(
        query,
        top_k=top_k,
        index_dir=SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
    )


METHODS: dict[str, Retriever] = {
    "keyword": retrieve_by_keyword_baseline,
    "bm25": retrieve_bm25_base,
    "bm25_semantic_metadata": retrieve_bm25_metadata,
    "embedding": retrieve_by_embedding,
    "metadata_embedding": retrieve_metadata_embedding,
    "linear_hybrid": hybrid_retrieve,
    "rrf_hybrid": hybrid_retrieve_rrf,
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        raise ValueError(f"Cases file must contain a JSON list of objects: {path}")
    if len(cases) != 48:
        raise ValueError(f"Expected 48 retrieval cases, found {len(cases)} in {path}")
    return cases


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def ndcg(retrieved: list[str], expected: set[str], k: int) -> float:
    gains = [1.0 if source in expected else 0.0 for source in retrieved[:k]]
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal_count = min(len(expected), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / idcg if idcg else 0.0


def metrics_for(retrieved: list[str], expected: set[str], ks: tuple[int, ...]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for k in ks:
        selected = retrieved[:k]
        relevant = {source for source in selected if source in expected}
        metrics[f"hit@{k}"] = float(bool(relevant))
        metrics[f"recall@{k}"] = len(relevant) / len(expected) if expected else 0.0
        metrics[f"precision@{k}"] = len(relevant) / k if k else 0.0
        metrics[f"nDCG@{k}"] = ndcg(retrieved, expected, k)

    first_relevant = next(
        (rank for rank, source in enumerate(retrieved, start=1) if source in expected),
        0,
    )
    metrics["mrr@5"] = (
        1.0 / first_relevant
        if first_relevant and first_relevant <= 5
        else 0.0
    )
    metrics["mrr"] = 1.0 / first_relevant if first_relevant else 0.0
    return metrics


def serializable_chunk(item: dict[str, Any], rank: int, method: str) -> dict[str, Any]:
    chunk: dict[str, Any] = {
        "source": str(item.get("source", "")),
        "rank": rank,
        "retrieval_method": item.get("retrieval_method", method),
    }
    for key in (
        "title", "chapter_title", "section_title", "score", "keyword_score",
        "bm25_score", "embedding_score", "embedding_cosine_score",
        "hybrid_score", "rrf_score", "keyword_rank", "embedding_rank",
        "normalized_bm25_score", "normalized_embedding_cosine_score", "rrf_sources",
    ):
        if key in item:
            chunk[key] = item[key]
    return chunk


def evaluate_case(
    case: dict[str, Any],
    retriever: Retriever,
    method: str,
    top_k: int,
    ks: tuple[int, ...],
) -> dict[str, Any]:
    expected_sources = list(dict.fromkeys(str(source) for source in case["expected_sources"]))
    expected = set(expected_sources)
    started = time.perf_counter()
    results = retriever(str(case["query"]), top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    chunks = [serializable_chunk(item, rank, method) for rank, item in enumerate(results[:top_k], 1)]
    retrieved_sources = [chunk["source"] for chunk in chunks]
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query_type": case.get("query_type", ""),
        "difficulty": case.get("difficulty", ""),
        "query": str(case["query"]),
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "metrics": metrics_for(retrieved_sources, expected, ks),
        "retrieval_time_ms": elapsed_ms,
        "top_k_chunks": chunks,
    }


def summarize(case_results: list[dict[str, Any]]) -> dict[str, float | int]:
    keys = list(case_results[0]["metrics"]) if case_results else []
    return {
        "cases": len(case_results),
        **{key: mean([float(case["metrics"][key]) for case in case_results]) for key in keys},
        "average_retrieval_time_ms": mean(
            [float(case["retrieval_time_ms"]) for case in case_results]
        ),
    }


def method_config(method: str, top_k: int, ks: tuple[int, ...]) -> dict[str, Any]:
    config: dict[str, Any] = {"top_k": top_k, "ks": list(ks)}
    if method == "keyword":
        config["retriever"] = "keyword baseline"
    elif method == "bm25":
        config.update({"metadata_mode": "base"})
    elif method == "bm25_semantic_metadata":
        config.update({"metadata_mode": PRODUCTION_BM25_METADATA_MODE})
    elif method == "embedding":
        config.update({"index_dir": str(BASE_VECTOR_INDEX_DIR), "embedding_model": get_embedding_model_name()})
    elif method == "metadata_embedding":
        config.update({"index_dir": str(SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR), "embedding_model": get_embedding_model_name()})
    elif method == "linear_hybrid":
        config.update({
            "keyword_weight": KEYWORD_WEIGHT,
            "embedding_weight": EMBEDDING_WEIGHT,
            "candidate_k": max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES),
        })
    elif method == "rrf_hybrid":
        config.update({
            "rrf_k": RRF_K,
            "candidate_k": max(top_k * RRF_CANDIDATE_MULTIPLIER, RRF_MIN_CANDIDATES),
        })
    return config


def markdown_summary(
    report: dict[str, Any],
    report_path: Path,
    markdown_path: Path,
) -> None:
    summary_keys = (
        "hit@1",
        "hit@3",
        "hit@5",
        "recall@5",
        "recall@10",
        "mrr@5",
        "nDCG@5",
        "nDCG@10",
    )
    summaries = {
        method: result["summary"]
        for method, result in report["strategies"].items()
    }
    best_methods = {
        key: max(summaries, key=lambda method: float(summaries[method].get(key, 0.0)))
        for key in summary_keys
    }

    lines = [
        "# Retrieval Benchmark Summary",
        "",
        "## Benchmark information",
        "",
        f"- Timestamp (UTC): `{report['timestamp_utc']}`",
        f"- Cases: `{len(report['strategies'][next(iter(report['strategies']))]['cases'])}`",
        f"- Top K: `{report['top_k']}`",
        f"- Case file: `{report['cases_path']}`",
        f"- JSON report: `{report_path}`",
        "",
        "## Retrieval method configurations",
        "",
        "| Method | Configuration |",
        "| --- | --- |",
    ]
    for method, result in report["strategies"].items():
        config = ", ".join(f"{key}=`{value}`" for key, value in result["config"].items())
        lines.append(f"| `{method}` | {config} |")

    lines.extend([
        "",
        "## Summary",
        "",
        "Best values are bolded.",
        "",
        "| Method | Hit@1 | Hit@3 | Hit@5 | Recall@5 | Recall@10 | MRR@5 | nDCG@5 | nDCG@10 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for method, summary in summaries.items():
        cells = []
        for key in summary_keys:
            value = float(summary.get(key, 0.0))
            rendered = f"{value:.3f}"
            if best_methods[key] == method:
                rendered = f"**{rendered}**"
            cells.append(rendered)
        lines.append(f"| `{method}` | " + " | ".join(cells) + " |")

    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reset_retrieval_caches() -> None:
    clear_bm25_caches()
    get_cached_vector_index.cache_clear()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the offline retrieval benchmark against the production retrievers."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--experiments", type=Path, default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--methods", nargs="+", choices=tuple(METHODS), default=list(METHODS))
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")

    ks = tuple(k for k in DEFAULT_KS if k <= args.top_k)
    if args.top_k not in ks:
        ks += (args.top_k,)
    cases = load_cases(args.cases)
    reset_retrieval_caches()

    started = time.perf_counter()
    strategies: dict[str, Any] = {}
    for method in args.methods:
        evaluated = [
            evaluate_case(case, METHODS[method], method, args.top_k, ks)
            for case in cases
        ]
        strategies[method] = {
            "config": {"top_k": args.top_k, "ks": list(ks)},
            "summary": summarize(evaluated),
            "cases": evaluated,
        }

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    report_path = args.report_dir / f"retrieval_benchmark_{timestamp}.json"
    markdown_path = args.report_dir / f"retrieval_benchmark_{timestamp}.md"
    report = {
        "schema_version": "retrieval_benchmark_v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases_path": str(args.cases),
        "top_k": args.top_k,
        "ks": list(ks),
        "elapsed_seconds": time.perf_counter() - started,
        "strategies": strategies,
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    markdown_report = {
        **report,
        "strategies": {
            method: {
                **result,
                "config": method_config(method, args.top_k, ks),
            }
            for method, result in strategies.items()
        },
    }
    report["strategies"] = markdown_report["strategies"]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_summary(report, report_path, markdown_path)

    experiment = {
        "experiment": "retrieval_benchmark_v1",
        "timestamp_utc": report["timestamp_utc"],
        "cases": str(args.cases),
        "report": str(report_path),
        "markdown_report": str(markdown_path),
        "top_k": args.top_k,
        "methods": list(args.methods),
        "strategies": {method: result["summary"] for method, result in strategies.items()},
    }
    args.experiments.parent.mkdir(parents=True, exist_ok=True)
    with args.experiments.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(experiment, ensure_ascii=False) + "\n")

    print(f"report: {report_path}")
    print(f"markdown: {markdown_path}")
    print(f"experiments: {args.experiments}")
    print("| method | cases | hit@5 | recall@5 | precision@5 | mrr | nDCG@5 |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for method, result in strategies.items():
        summary = result["summary"]
        print(
            f"| {method} | {summary['cases']} | {summary.get('hit@5', 0):.3f} | "
            f"{summary.get('recall@5', 0):.3f} | {summary.get('precision@5', 0):.3f} | "
            f"{summary.get('mrr', 0):.3f} | {summary.get('nDCG@5', 0):.3f} |"
        )


if __name__ == "__main__":
    main()
