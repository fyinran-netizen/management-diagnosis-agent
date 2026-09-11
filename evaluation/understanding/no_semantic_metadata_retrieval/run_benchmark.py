from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.retrievers.bm25 import (  # noqa: E402
    clear_bm25_caches,
    retrieve_by_bm25,
)
from app.tools.retrieval.retrievers.embedding import (  # noqa: E402
    get_cached_vector_index,
    retrieve_by_embedding,
)
from app.tools.retrieval.vector_store import BASE_VECTOR_INDEX_DIR  # noqa: E402
from app.tools.understanding import understand_query  # noqa: E402
from scripts.run_retrieval_benchmark import (  # noqa: E402
    DEFAULT_KS,
    load_cases,
    metrics_for,
    serializable_chunk,
    summarize,
)

import importlib  # noqa: E402


linear_module = importlib.import_module("app.tools.retrieval.retrievers.hybrid_linear")
rrf_module = importlib.import_module("app.tools.retrieval.retrievers.hybrid_rrf")

DEFAULT_CASES = PROJECT_ROOT / "evaluation" / "retrieval" / "cases" / "retrieval_cases.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "evaluation" / "understanding" / "no_semantic_metadata_retrieval"
INTAKE_STRATEGIES = ("raw", "rule_based", "rewrite")
RETRIEVER_NAMES = ("bm25", "embedding", "hybrid_linear", "hybrid_rrf")
PRIMARY_METRICS = (
    "hit@1", "hit@3", "hit@5", "recall@5", "recall@10",
    "mrr@5", "nDCG@5", "nDCG@10",
)
RULE_BASED_GOAL = (
    "Please identify the main management problems, analyze possible root causes, "
    "and provide practical next-step recommendations."
)
Retriever = Callable[[str, int], list[dict[str, Any]]]


def retrieve_bm25_no_metadata(query: str, top_k: int) -> list[dict[str, Any]]:
    return retrieve_by_bm25(query, top_k=top_k, metadata_mode="base")


def retrieve_embedding_no_metadata(query: str, top_k: int) -> list[dict[str, Any]]:
    return retrieve_by_embedding(query, top_k=top_k, index_dir=BASE_VECTOR_INDEX_DIR)


def retrieve_linear_no_metadata(query: str, top_k: int) -> list[dict[str, Any]]:
    # hybrid_retrieve itself is the production implementation. Its imported
    # child retrievers are rebound only for this benchmark invocation so both
    # branches use the no-semantic-metadata configuration.
    with (
        patch.object(linear_module, "retrieve_by_bm25", retrieve_bm25_no_metadata),
        patch.object(linear_module, "retrieve_by_embedding", retrieve_embedding_no_metadata),
    ):
        return linear_module.hybrid_retrieve(query=query, hybrid_top_k=top_k)


def retrieve_rrf_no_metadata(query: str, top_k: int) -> list[dict[str, Any]]:
    with (
        patch.object(rrf_module, "retrieve_by_bm25", retrieve_bm25_no_metadata),
        patch.object(rrf_module, "retrieve_by_embedding", retrieve_embedding_no_metadata),
    ):
        return rrf_module.hybrid_retrieve_rrf(query=query, top_k=top_k)


RETRIEVERS: dict[str, Retriever] = {
    "bm25": retrieve_bm25_no_metadata,
    "embedding": retrieve_embedding_no_metadata,
    "hybrid_linear": retrieve_linear_no_metadata,
    "hybrid_rrf": retrieve_rrf_no_metadata,
}


def evaluate_case(
    case: dict[str, Any],
    retriever: Retriever,
    retriever_name: str,
    intake_strategy: str,
    top_k: int,
    ks: tuple[int, ...],
) -> dict[str, Any]:
    original_query = str(case["query"])
    goal = RULE_BASED_GOAL if intake_strategy == "rule_based" else None
    understanding = understand_query(
        original_query,
        mode=intake_strategy,
        goal=goal,
    )
    retrieval_query = understanding["retrieval_query"]

    started = time.perf_counter()
    results = retriever(retrieval_query, top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    expected_sources = list(dict.fromkeys(str(source) for source in case["expected_sources"]))
    expected = set(expected_sources)
    chunks = [
        serializable_chunk(item, rank, retriever_name)
        for rank, item in enumerate(results[:top_k], 1)
    ]
    retrieved_sources = [chunk["source"] for chunk in chunks]
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query_type": case.get("query_type", ""),
        "difficulty": case.get("difficulty", ""),
        "original_query": original_query,
        "understanding": understanding,
        "retrieval_query": retrieval_query,
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "metrics": metrics_for(retrieved_sources, expected, ks),
        "retrieval_time_ms": elapsed_ms,
        "top_k_chunks": chunks,
    }


def metric_delta(raw: dict[str, Any], comparison: dict[str, Any]) -> dict[str, float]:
    return {
        key: float(comparison.get(key, 0.0)) - float(raw.get(key, 0.0))
        for key in PRIMARY_METRICS
    }


def add_delta_vs_raw(
    strategy_cases: list[dict[str, Any]], raw_cases: list[dict[str, Any]]
) -> None:
    for case, raw_case in zip(strategy_cases, raw_cases, strict=True):
        case["delta_vs_raw"] = metric_delta(raw_case["metrics"], case["metrics"])


def retriever_config(name: str, top_k: int, ks: tuple[int, ...]) -> dict[str, Any]:
    config: dict[str, Any] = {
        "retriever": name,
        "top_k": top_k,
        "ks": list(ks),
        "semantic_metadata": False,
    }
    if name == "bm25":
        config["metadata_mode"] = "base"
    elif name == "embedding":
        config["index_dir"] = str(BASE_VECTOR_INDEX_DIR)
    elif name == "hybrid_linear":
        config.update({
            "bm25_metadata_mode": "base",
            "embedding_index_dir": str(BASE_VECTOR_INDEX_DIR),
            "implementation": "app.tools.retrieval.retrievers.hybrid_linear.hybrid_retrieve",
        })
    elif name == "hybrid_rrf":
        config.update({
            "bm25_metadata_mode": "base",
            "embedding_index_dir": str(BASE_VECTOR_INDEX_DIR),
            "implementation": "app.tools.retrieval.retrievers.hybrid_rrf.hybrid_retrieve_rrf",
        })
    return config


def write_markdown(report: dict[str, Any], path: Path) -> None:
    columns = (
        ("Hit@1", "hit@1"), ("Hit@3", "hit@3"), ("Hit@5", "hit@5"),
        ("Recall@5", "recall@5"), ("Recall@10", "recall@10"),
        ("MRR@5", "mrr@5"), ("nDCG@5", "nDCG@5"), ("nDCG@10", "nDCG@10"),
    )
    labels = {"raw": "Raw", "rule_based": "Rule-based", "rewrite": "Rewrite"}
    lines = [
        "# Intake Strategy × Retrieval (No Semantic Metadata)",
        "",
        "## Benchmark information",
        "",
        f"- Timestamp (UTC): `{report['timestamp_utc']}`",
        f"- Cases: `{report['case_count']}`",
        f"- Top K: `{report['top_k']}`",
        f"- Case file (reused): `{report['cases_path']}`",
        f"- JSON report: `{report['json_report']}`",
        "- Semantic metadata: `false` for every retriever configuration.",
        "- Metrics and case set are reused from `scripts.run_retrieval_benchmark`.",
        "",
    ]
    for retriever in report["retrievers"]:
        result = report["strategies"][retriever]
        lines.extend([
            f"## `{retriever}`",
            "",
            "Configuration: " + ", ".join(
                f"`{key}={value}`" for key, value in result["config"].items()
            ),
            "",
            "| Intake strategy | " + " | ".join(label for label, _ in columns) + " |",
            "| --- | " + " | ".join(["---:"] * len(columns)) + " |",
        ])
        for strategy in INTAKE_STRATEGIES:
            summary = result["strategies"][strategy]["summary"]
            lines.append(
                f"| {labels[strategy]} | "
                + " | ".join(f"{float(summary.get(key, 0.0)):.3f}" for _, key in columns)
                + " |"
            )
        for strategy, delta_key in (("rule_based", "rule_based_vs_raw"), ("rewrite", "rewrite_vs_raw")):
            delta = result["delta"][delta_key]
            lines.append(
                f"| {labels[strategy]} vs Raw delta | "
                + " | ".join(f"{float(delta[key]):+.3f}" for _, key in columns)
                + " |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark intake strategies with semantic metadata disabled."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument(
        "--retrievers", nargs="+", choices=RETRIEVER_NAMES,
        default=list(RETRIEVER_NAMES),
    )
    args = parser.parse_args()
    if args.top_k < 10:
        parser.error("--top-k must be >= 10 for Recall@10 and nDCG@10")

    cases = load_cases(args.cases)
    ks = tuple(k for k in DEFAULT_KS if k <= args.top_k)
    started = time.perf_counter()
    clear_bm25_caches()
    get_cached_vector_index.cache_clear()

    strategies: dict[str, Any] = {}
    for retriever_name in args.retrievers:
        intake_results: dict[str, Any] = {}
        for intake_strategy in INTAKE_STRATEGIES:
            evaluated = [
                evaluate_case(
                    case, RETRIEVERS[retriever_name], retriever_name,
                    intake_strategy, args.top_k, ks,
                )
                for case in cases
            ]
            intake_results[intake_strategy] = {
                "summary": summarize(evaluated),
                "cases": evaluated,
            }
        raw_cases = intake_results["raw"]["cases"]
        for intake_strategy in ("rule_based", "rewrite"):
            add_delta_vs_raw(intake_results[intake_strategy]["cases"], raw_cases)
        for raw_case in raw_cases:
            raw_case["delta_vs_raw"] = {key: 0.0 for key in PRIMARY_METRICS}
        strategies[retriever_name] = {
            "config": retriever_config(retriever_name, args.top_k, ks),
            "strategies": intake_results,
            "delta": {
                "rule_based_vs_raw": metric_delta(
                    intake_results["raw"]["summary"], intake_results["rule_based"]["summary"]
                ),
                "rewrite_vs_raw": metric_delta(
                    intake_results["raw"]["summary"], intake_results["rewrite"]["summary"]
                ),
            },
        }

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"intake_no_semantic_metadata_{timestamp}.json"
    markdown_path = args.output_dir / f"intake_no_semantic_metadata_{timestamp}.md"
    report: dict[str, Any] = {
        "schema_version": "intake_retrieval_no_semantic_metadata_v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases_path": str(args.cases),
        "case_count": len(cases),
        "top_k": args.top_k,
        "ks": list(ks),
        "intake_strategies": list(INTAKE_STRATEGIES),
        "retrievers": list(args.retrievers),
        "semantic_metadata": False,
        "elapsed_seconds": time.perf_counter() - started,
        "strategies": strategies,
    }
    report["json_report"] = str(json_path)
    report["markdown_report"] = str(markdown_path)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, markdown_path)

    print(f"json: {json_path}")
    print(f"markdown: {markdown_path}")
    print("| retriever | intake | Hit@5 | Recall@5 | MRR@5 | nDCG@5 |")
    print("| --- | --- | ---: | ---: | ---: | ---: |")
    for retriever in args.retrievers:
        for intake_strategy in INTAKE_STRATEGIES:
            summary = strategies[retriever]["strategies"][intake_strategy]["summary"]
            print(
                f"| {retriever} | {intake_strategy} | {summary['hit@5']:.3f} | "
                f"{summary['recall@5']:.3f} | {summary['mrr@5']:.3f} | "
                f"{summary['nDCG@5']:.3f} |"
            )
        for delta_name in ("rule_based_vs_raw", "rewrite_vs_raw"):
            delta = strategies[retriever]["delta"][delta_name]
            print(
                f"| {retriever} | {delta_name} | {delta['hit@5']:+.3f} | "
                f"{delta['recall@5']:+.3f} | {delta['mrr@5']:+.3f} | "
                f"{delta['nDCG@5']:+.3f} |"
            )


if __name__ == "__main__":
    main()
