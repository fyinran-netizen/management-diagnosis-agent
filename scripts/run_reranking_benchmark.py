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

from app.tools.retrieval.pipeline import retrieve_pipeline  # noqa: E402
from app.tools.retrieval.rerankers.bge_reranker import (  # noqa: E402
    get_reranker_model_name,
)
from app.tools.retrieval.retrievers.hybrid_linear import (  # noqa: E402
    CANDIDATE_MULTIPLIER,
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    MIN_CANDIDATES,
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
METRIC_KEYS = (
    "hit@1",
    "hit@3",
    "hit@5",
    "recall@5",
    "recall@10",
    "precision@5",
    "mrr@5",
    "nDCG@5",
    "nDCG@10",
)
STRATEGIES = {
    "baseline": False,
    "rerank": True,
}


def evaluate_case(
    case: dict[str, Any],
    *,
    use_reranker: bool,
    candidate_top_k: int,
    final_top_k: int,
) -> dict[str, Any]:
    expected_sources = list(dict.fromkeys(str(source) for source in case["expected_sources"]))
    expected = set(expected_sources)
    started = time.perf_counter()
    results = retrieve_pipeline(
        query=str(case["query"]),
        candidate_top_k=candidate_top_k,
        final_top_k=final_top_k,
        use_reranker=use_reranker,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    chunks = [
        serializable_chunk(item, rank, "linear_hybrid_rerank" if use_reranker else "linear_hybrid")
        for rank, item in enumerate(results[:final_top_k], 1)
    ]
    retrieved_sources = [chunk["source"] for chunk in chunks]
    all_metrics = metrics_for(retrieved_sources, expected, (1, 3, 5, 10))
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query_type": case.get("query_type", ""),
        "difficulty": case.get("difficulty", ""),
        "query": str(case["query"]),
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "metrics": {key: all_metrics[key] for key in METRIC_KEYS},
        "retrieval_time_ms": elapsed_ms,
        "top_k_chunks": chunks,
    }


def strategy_config(use_reranker: bool, candidate_top_k: int, final_top_k: int) -> dict[str, Any]:
    config: dict[str, Any] = {
        "candidate_top_k": candidate_top_k,
        "final_top_k": final_top_k,
        "keyword_weight": KEYWORD_WEIGHT,
        "embedding_weight": EMBEDDING_WEIGHT,
        "hybrid_candidate_k": max(candidate_top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES),
        "use_reranker": use_reranker,
    }
    if use_reranker:
        config["reranker"] = get_reranker_model_name()
    return config


def write_markdown(report: dict[str, Any], report_path: Path, markdown_path: Path) -> None:
    summaries = {name: result["summary"] for name, result in report["strategies"].items()}
    best = {
        key: max(summaries, key=lambda name: float(summaries[name].get(key, 0.0)))
        for key in METRIC_KEYS
    }
    labels = {
        "baseline": "Baseline (linear hybrid)",
        "rerank": "Rerank (linear hybrid + BGE)",
    }
    columns = ("Hit@1", "Hit@3", "Hit@5", "Recall@5", "Recall@10", "Precision@5", "MRR@5", "nDCG@5", "nDCG@10")
    lines = [
        "# Reranking Benchmark Summary",
        "",
        "## Benchmark information",
        "",
        f"- Timestamp (UTC): `{report['timestamp_utc']}`",
        f"- Cases: `{report['case_count']}`",
        f"- Candidate top K: `{report['candidate_top_k']}`",
        f"- Final top K: `{report['final_top_k']}`",
        f"- Case file: `{report['cases_path']}`",
        f"- JSON report: `{report_path}`",
        "",
        "## Configuration",
        "",
        "Both strategies use the same cases, candidate_top_k, final_top_k, and linear hybrid weights.",
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
    metric_by_column = {column: key for column, key in zip(columns, METRIC_KEYS, strict=True)}
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
    parser = argparse.ArgumentParser(description="Benchmark linear hybrid retrieval with and without BGE reranking.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--experiments", type=Path, default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--candidate-top-k", type=int, default=DEFAULT_CANDIDATE_TOP_K)
    parser.add_argument("--final-top-k", type=int, default=DEFAULT_FINAL_TOP_K)
    args = parser.parse_args()
    if args.candidate_top_k < 1 or args.final_top_k < 1:
        parser.error("--candidate-top-k and --final-top-k must be >= 1")
    if args.final_top_k < 10:
        parser.error("--final-top-k must be >= 10 to calculate Recall@10 and nDCG@10")
    if args.candidate_top_k < args.final_top_k:
        parser.error("--candidate-top-k must be >= --final-top-k")

    cases = load_cases(args.cases)
    started = time.perf_counter()
    strategies: dict[str, Any] = {}
    for name, use_reranker in STRATEGIES.items():
        evaluated = [
            evaluate_case(
                case,
                use_reranker=use_reranker,
                candidate_top_k=args.candidate_top_k,
                final_top_k=args.final_top_k,
            )
            for case in cases
        ]
        strategies[name] = {
            "config": strategy_config(use_reranker, args.candidate_top_k, args.final_top_k),
            "summary": summarize(evaluated),
            "cases": evaluated,
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
        "candidate_top_k": args.candidate_top_k,
        "final_top_k": args.final_top_k,
        "metrics": list(METRIC_KEYS),
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
        "candidate_top_k": args.candidate_top_k,
        "final_top_k": args.final_top_k,
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
