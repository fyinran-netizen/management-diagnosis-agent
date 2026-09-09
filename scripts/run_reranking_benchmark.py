from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.rerankers.bge_reranker import (  # noqa: E402
    get_reranker_model_name,
    score_candidates,
)
from app.tools.retrieval.retrievers.hybrid_linear import (  # noqa: E402
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    hybrid_retrieve,
)
from scripts.run_retrieval_benchmark import (  # noqa: E402
    DEFAULT_CASES,
    DEFAULT_REPORT_DIR,
    DEFAULT_EXPERIMENTS,
    load_cases,
    metrics_for,
    serializable_chunk,
    summarize,
)


DEFAULT_CANDIDATE_TOP_K = 100
DEFAULT_FINAL_TOP_K = 20
PRIMARY_METRIC_KEYS = (
    "hit@1",
    "hit@3",
    "hit@5",
    "recall@5",
    "recall@10",
    "mrr@5",
    "nDCG@5",
    "nDCG@10",
)
CASE_METRIC_KEYS = (
    *PRIMARY_METRIC_KEYS,
    "precision@5",
    "candidate_pool_hit",
    "candidate_pool_recall",
)
STRATEGIES = {
    "baseline": False,
    "rerank": True,
}


def summarize_strategy(case_results: list[dict[str, Any]]) -> dict[str, float | int]:
    summary = summarize(case_results)
    summary = {
        key: value
        for key, value in summary.items()
        if key in PRIMARY_METRIC_KEYS or key in {"cases", "average_retrieval_time_ms"}
    }
    summary.update({
        "average_candidate_retrieval_ms": (
            sum(float(case["candidate_retrieval_ms"]) for case in case_results) / len(case_results)
            if case_results else 0.0
        ),
        "average_rerank_scoring_ms": (
            sum(float(case["rerank_scoring_ms"]) for case in case_results) / len(case_results)
            if case_results else 0.0
        ),
    })
    return summary


def evaluate_case(
    case: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
    use_reranker: bool,
    final_top_k: int,
    candidate_retrieval_ms: float,
    rerank_scoring_ms: float,
) -> dict[str, Any]:
    expected_sources = list(dict.fromkeys(str(source) for source in case["expected_sources"]))
    expected = set(expected_sources)
    candidate_sources = [str(item.get("source", "")) for item in candidates]
    candidate_relevant = {source for source in candidate_sources if source in expected}
    candidate_pool_metrics = {
        "candidate_pool_hit": float(bool(candidate_relevant)),
        "candidate_pool_recall": len(candidate_relevant) / len(expected) if expected else 0.0,
    }
    results = candidates[:final_top_k]
    chunks = [
        serializable_chunk(item, rank, "linear_hybrid_rerank" if use_reranker else "linear_hybrid")
        for rank, item in enumerate(results[:final_top_k], 1)
    ]
    for chunk, item in zip(chunks, results, strict=True):
        if "rerank_score" in item:
            chunk["rerank_score"] = item["rerank_score"]
    retrieved_sources = [chunk["source"] for chunk in chunks]
    all_metrics = metrics_for(retrieved_sources, expected, (1, 3, 5, 10))
    all_metrics.update(candidate_pool_metrics)
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query_type": case.get("query_type", ""),
        "difficulty": case.get("difficulty", ""),
        "query": str(case["query"]),
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "metrics": {key: all_metrics[key] for key in CASE_METRIC_KEYS},
        "retrieval_time_ms": candidate_retrieval_ms + rerank_scoring_ms,
        "candidate_retrieval_ms": candidate_retrieval_ms,
        "rerank_scoring_ms": rerank_scoring_ms,
        "candidate_pool_size": len(candidates),
        "candidate_pool_sources": candidate_sources,
        "top_k_chunks": chunks,
    }


def strategy_config(
    use_reranker: bool,
    hybrid_candidate_k: int,
    final_k: int,
    source_retrieval_k: int | None,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "hybrid_candidate_k": hybrid_candidate_k,
        "final_k": final_k,
        "source_retrieval_k": source_retrieval_k,
        "keyword_weight": KEYWORD_WEIGHT,
        "embedding_weight": EMBEDDING_WEIGHT,
        "use_reranker": use_reranker,
    }
    if use_reranker:
        config["reranker"] = get_reranker_model_name()
    return config


def write_markdown(report: dict[str, Any], report_path: Path, markdown_path: Path) -> None:
    summaries = {name: result["summary"] for name, result in report["strategies"].items()}
    best = {
        key: max(summaries, key=lambda name: float(summaries[name].get(key, 0.0)))
        for key in PRIMARY_METRIC_KEYS
    }
    labels = {
        "baseline": "Baseline (linear hybrid)",
        "rerank": "Rerank (linear hybrid + BGE)",
    }
    columns = (
        "Hit@1", "Hit@3", "Hit@5", "Recall@5", "Recall@10",
        "MRR@5", "nDCG@5", "nDCG@10",
    )
    lines = [
        "# Reranking Benchmark Summary",
        "",
        "## Benchmark information",
        "",
        f"- Timestamp (UTC): `{report['timestamp_utc']}`",
        f"- Cases: `{report['case_count']}`",
        f"- Hybrid candidate K: `{report['hybrid_candidate_k']}`",
        f"- Final K: `{report['final_k']}`",
        f"- Source retrieval K: `{report['source_retrieval_k']}`",
        f"- Case file: `{report['cases_path']}`",
        f"- JSON report: `{report_path}`",
        "",
        "## Configuration",
        "",
        "Baseline = Hybrid \u539f\u6392\u5e8f\u3002",
        "Hybrid + Rerank = \u540c\u4e00\u5019\u9009\u96c6\u7ecf\u8fc7 BGE \u91cd\u6392\u3002",
        "Both strategies use the same hybrid candidate pool and linear hybrid weights; Hybrid retrieval runs once per case.",
        "",
        "| Strategy | Configuration |",
        "| --- | --- |",
    ]
    for name, result in report["strategies"].items():
        config = ", ".join(f"{key}=`{value}`" for key, value in result["config"].items())
        lines.append(f"| `{labels[name]}` | {config} |")
    lines.extend([
        "",
        "## Baseline vs rerank",
        "",
        "Best values are bolded.",
        "",
        "| Strategy | " + " | ".join(columns) + " |",
        "| --- | " + " | ".join([":---:"] * len(columns)) + " |",
    ])
    metric_by_column = {column: key for column, key in zip(columns, PRIMARY_METRIC_KEYS, strict=True)}
    for name, summary in summaries.items():
        values = []
        for column in columns:
            key = metric_by_column[column]
            rendered = f"{float(summary.get(key, 0.0)):.3f}"
            if best[key] == name:
                rendered = f"**{rendered}**"
            values.append(rendered)
        lines.append(f"| `{labels[name]}` | " + " | ".join(values) + " |")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark one hybrid candidate retrieval with and without BGE reranking.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--experiments", type=Path, default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--hybrid-candidate-k", type=int, default=DEFAULT_CANDIDATE_TOP_K)
    parser.add_argument("--final-k", type=int, default=DEFAULT_FINAL_TOP_K)
    parser.add_argument("--source-retrieval-k", type=int, default=None)
    args = parser.parse_args()
    if args.hybrid_candidate_k < 1 or args.final_k < 1:
        parser.error("--hybrid-candidate-k and --final-k must be >= 1")
    if args.source_retrieval_k is not None and args.source_retrieval_k < 1:
        parser.error("--source-retrieval-k must be >= 1")
    if args.final_k < 10:
        parser.error("--final-k must be >= 10 to calculate Recall@10 and nDCG@10")
    if args.hybrid_candidate_k < args.final_k:
        parser.error("--hybrid-candidate-k must be >= --final-k")

    cases = load_cases(args.cases)
    started = time.perf_counter()
    evaluated_by_strategy = {name: [] for name in STRATEGIES}
    for case in cases:
        retrieval_started = time.perf_counter()
        candidates = hybrid_retrieve(
            query=str(case["query"]),
            hybrid_top_k=args.hybrid_candidate_k,
            source_retrieval_k=args.source_retrieval_k,
        )
        candidate_retrieval_ms = (time.perf_counter() - retrieval_started) * 1000.0

        baseline_case = evaluate_case(
            case,
            candidates=candidates,
            use_reranker=False,
            final_top_k=args.final_k,
            candidate_retrieval_ms=candidate_retrieval_ms,
            rerank_scoring_ms=0.0,
        )
        scoring_started = time.perf_counter()
        reranked_candidates = score_candidates(query=str(case["query"]), candidates=candidates)
        rerank_scoring_ms = (time.perf_counter() - scoring_started) * 1000.0
        rerank_case = evaluate_case(
            case,
            candidates=sorted(
                reranked_candidates,
                key=lambda item: float(item.get("rerank_score", 0.0)),
                reverse=True,
            ),
            use_reranker=True,
            final_top_k=args.final_k,
            candidate_retrieval_ms=candidate_retrieval_ms,
            rerank_scoring_ms=rerank_scoring_ms,
        )
        evaluated_by_strategy["baseline"].append(baseline_case)
        evaluated_by_strategy["rerank"].append(rerank_case)

    strategies = {
        name: {
            "config": strategy_config(
                use_reranker,
                args.hybrid_candidate_k,
                args.final_k,
                args.source_retrieval_k,
            ),
            "summary": summarize_strategy(evaluated_by_strategy[name]),
            "cases": evaluated_by_strategy[name],
        }
        for name, use_reranker in STRATEGIES.items()
    }

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report_path = args.report_dir / f"reranking_benchmark_{timestamp}.json"
    markdown_path = args.report_dir / f"reranking_benchmark_{timestamp}.md"
    report = {
        "schema_version": "reranking_benchmark_v1",
        "timestamp_utc": timestamp_utc,
        "cases_path": str(args.cases),
        "case_count": len(cases),
        "hybrid_candidate_k": args.hybrid_candidate_k,
        "final_k": args.final_k,
        "source_retrieval_k": args.source_retrieval_k,
        "metrics": list(PRIMARY_METRIC_KEYS),
        "elapsed_seconds": time.perf_counter() - started,
        "strategies": strategies,
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, report_path, markdown_path)

    experiment = {
        "experiment": "reranking_benchmark_v1",
        "timestamp_utc": timestamp_utc,
        "cases": str(args.cases),
        "report": str(report_path),
        "markdown_report": str(markdown_path),
        "hybrid_candidate_k": args.hybrid_candidate_k,
        "final_k": args.final_k,
        "source_retrieval_k": args.source_retrieval_k,
        "strategies": {name: result["summary"] for name, result in strategies.items()},
    }
    args.experiments.parent.mkdir(parents=True, exist_ok=True)
    with args.experiments.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(experiment, ensure_ascii=False) + "\n")

    print(f"report: {report_path}")
    print(f"markdown: {markdown_path}")
    print(f"experiments: {args.experiments}")


if __name__ == "__main__":
    main()
