from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval import tool as retrieval_tool  # noqa: E402
from app.tools.retrieval.retrievers.hybrid_linear import hybrid_retrieve  # noqa: E402
from app.tools.understanding import understand_query  # noqa: E402
from app.tools.retrieval.tool import retrieve_relevant_chunks  # noqa: E402
from scripts.run_retrieval_benchmark import (  # noqa: E402
    DEFAULT_KS,
    load_cases,
    metrics_for,
    serializable_chunk,
    summarize,
)
from evaluation.retrieval.relevance import relevance_for  # noqa: E402


DEFAULT_CASES = PROJECT_ROOT / "evaluation" / "retrieval" / "cases" / "retrieval_cases.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "evaluation" / "understanding" / "best_retrieval_baseline"
RULE_BASED_GOAL = (
    "Please identify the main management problems, analyze possible root causes, "
    "and provide practical next-step recommendations."
)
PRIMARY_METRICS = (
    "hit@1", "hit@3", "hit@5", "recall@5", "recall@10",
    "mrr@5", "nDCG@5", "nDCG@10",
)


def linear_hybrid_pipeline(
    query: str,
    *,
    mode: str = "hybrid_rerank",
    hybrid_candidate_k: int | None = None,
    final_k: int = 5,
    final_top_k: int | None = None,
    source_retrieval_k: int | None = None,
) -> list[dict[str, Any]]:
    """Adapter used only while this benchmark calls the public retrieval tool.

    The public tool currently defaults to the rerank pipeline. This benchmark
    must measure the established no-reranker linear-hybrid baseline, so its
    imported pipeline binding is replaced locally for the duration of a run.
    The production retrieval module is not changed.
    """
    del mode, hybrid_candidate_k
    if final_top_k is not None:
        final_k = final_top_k
    return hybrid_retrieve(
        query=query,
        hybrid_top_k=final_k,
        source_retrieval_k=source_retrieval_k,
    )


def evaluate_case(case: dict[str, Any], mode: str, top_k: int) -> dict[str, Any]:
    query = str(case["query"])
    goal = RULE_BASED_GOAL if mode == "rule_based" else None
    understanding = understand_query(query, mode=mode, goal=goal)
    retrieval_query = understanding["retrieval_query"]

    started = time.perf_counter()
    chunks = retrieve_relevant_chunks(retrieval_query, top_k=top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    gold_evidence = [str(evidence) for evidence in case["gold_evidence"]]
    serialized = [
        serializable_chunk(item, rank, "linear_hybrid")
        for rank, item in enumerate(chunks[:top_k], 1)
    ]
    retrieved_sources = [item["source"] for item in serialized]
    relevant, covered_by_rank = relevance_for(chunks[:top_k], gold_evidence)
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query_type": case.get("query_type", ""),
        "difficulty": case.get("difficulty", ""),
        "query": query,
        "understanding": understanding,
        "retrieval_query": retrieval_query,
        "gold_evidence": gold_evidence,
        "retrieved_sources": retrieved_sources,
        "metrics": metrics_for(relevant, covered_by_rank, len(gold_evidence), tuple(k for k in DEFAULT_KS if k <= top_k)),
        "retrieval_time_ms": elapsed_ms,
        "top_k_chunks": serialized,
    }


def delta_summary(raw: dict[str, Any], comparison: dict[str, Any]) -> dict[str, float]:
    return {
        key: float(comparison.get(key, 0.0)) - float(raw.get(key, 0.0))
        for key in PRIMARY_METRICS
    }


def add_case_deltas(cases: list[dict[str, Any]], raw_cases: list[dict[str, Any]]) -> None:
    for case, raw_case in zip(cases, raw_cases, strict=True):
        case["delta_vs_raw"] = delta_summary(raw_case["metrics"], case["metrics"])


def add_pair_delta(
    cases: list[dict[str, Any]],
    other_cases: list[dict[str, Any]],
    field: str,
) -> None:
    for case, other_case in zip(cases, other_cases, strict=True):
        case[field] = delta_summary(other_case["metrics"], case["metrics"])


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summaries = {name: value["summary"] for name, value in report["strategies"].items()}
    labels = {"raw": "Raw", "rule_based": "Rule-based", "rewrite": "Rewrite"}
    columns = (
        ("Hit@1", "hit@1"), ("Hit@3", "hit@3"), ("Hit@5", "hit@5"),
        ("Recall@5", "recall@5"), ("Recall@10", "recall@10"),
        ("MRR@5", "mrr@5"), ("nDCG@5", "nDCG@5"), ("nDCG@10", "nDCG@10"),
    )
    lines = [
        "# Understanding Strategy × Best Retrieval Baseline",
        "",
        "## Benchmark information",
        "",
        f"- Timestamp (UTC): `{report['timestamp_utc']}`",
        f"- Cases: `{report['case_count']}`",
        f"- Top K: `{report['top_k']}`",
        f"- Case file (reused): `{report['cases_path']}`",
        f"- JSON report: `{report['json_report']}`",
        "- Retrieval: metadata-enhanced BM25 + base embedding + linear hybrid; reranker and generation disabled.",
        "",
        "## Aggregate metrics",
        "",
        "Delta rows compare each strategy with raw.",
        "",
        "| Strategy | " + " | ".join(label for label, _ in columns) + " |",
        "| --- | " + " | ".join(["---:"] * len(columns)) + " |",
    ]
    for name in ("raw", "rule_based", "rewrite"):
        summary = summaries[name]
        lines.append(
            f"| {labels[name]} | "
            + " | ".join(f"{float(summary.get(key, 0.0)):.3f}" for _, key in columns)
            + " |"
        )
    for name in ("rule_based_vs_raw", "rewrite_vs_raw"):
        delta = report["delta"][name]
        lines.append(
            f"| Delta ({name.replace('_', ' ')}) | "
            + " | ".join(f"{float(delta[key]):+.3f}" for _, key in columns)
            + " |"
        )
    lines.extend([
        "",
        "## Configuration",
        "",
        f"- rule_based goal: `{RULE_BASED_GOAL}`",
        "- Each case runs raw, rule_based, and rewrite independently through `understand_query(...)`, then the resulting retrieval query through `retrieve_relevant_chunks(...)`.",
        "- No LangGraph, generation, reranker, or case-file copy is used.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Understanding strategies against the best retrieval baseline.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=20)
    args = parser.parse_args()
    if args.top_k < 10:
        parser.error("--top-k must be >= 10 for Recall@10 and nDCG@10")

    cases = load_cases(args.cases)
    started = time.perf_counter()
    strategies: dict[str, Any] = {}
    with patch.object(retrieval_tool, "retrieve_pipeline", linear_hybrid_pipeline):
        for mode in ("raw", "rule_based", "rewrite"):
            results = [evaluate_case(case, mode, args.top_k) for case in cases]
            strategies[mode] = {
                "config": {
                    "understanding_mode": mode,
                    "goal": RULE_BASED_GOAL if mode == "rule_based" else None,
                    "retrieval": "metadata-enhanced BM25 + base embedding + linear hybrid",
                    "reranker": False,
                    "generation": False,
                    "top_k": args.top_k,
                },
                "summary": summarize(results),
                "cases": results,
            }

        add_case_deltas(strategies["rule_based"]["cases"], strategies["raw"]["cases"])
        add_case_deltas(strategies["rewrite"]["cases"], strategies["raw"]["cases"])
        add_pair_delta(
            strategies["rewrite"]["cases"],
            strategies["rule_based"]["cases"],
            "delta_vs_rule_based",
        )

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"understanding_benchmark_{timestamp}.json"
    markdown_path = args.output_dir / f"understanding_benchmark_{timestamp}.md"
    report = {
        "schema_version": "understanding_best_retrieval_baseline_v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases_path": str(args.cases),
        "case_count": len(cases),
        "top_k": args.top_k,
        "ks": [k for k in DEFAULT_KS if k <= args.top_k],
        "retrieval_baseline": "metadata-enhanced BM25 + base embedding + linear hybrid",
        "langgraph": False,
        "generation": False,
        "reranker": False,
        "elapsed_seconds": time.perf_counter() - started,
        "strategies": strategies,
    }
    report["delta"] = {
        "rule_based_vs_raw": delta_summary(
            strategies["raw"]["summary"], strategies["rule_based"]["summary"]
        ),
        "rewrite_vs_raw": delta_summary(
            strategies["raw"]["summary"], strategies["rewrite"]["summary"]
        ),
        "rewrite_vs_rule_based": delta_summary(
            strategies["rule_based"]["summary"], strategies["rewrite"]["summary"]
        ),
    }
    report["json_report"] = str(json_path)
    report["markdown_report"] = str(markdown_path)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, markdown_path)
    print(f"json: {json_path}")
    print(f"markdown: {markdown_path}")
    print("| strategy | Hit@5 | Recall@5 | MRR@5 | nDCG@5 |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for mode in ("raw", "rule_based", "rewrite"):
        summary = strategies[mode]["summary"]
        print(f"| {mode} | {summary['hit@5']:.3f} | {summary['recall@5']:.3f} | {summary['mrr@5']:.3f} | {summary['nDCG@5']:.3f} |")


if __name__ == "__main__":
    main()
