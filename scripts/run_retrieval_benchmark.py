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
from app.core.config import PRIVATE_KNOWLEDGE_DIR  # noqa: E402
from evaluation.retrieval.relevance import relevance_for  # noqa: E402
from evaluation.retrieval.evidence import load_cases as load_cases_with_evidence  # noqa: E402


DEFAULT_CASES = PROJECT_ROOT / "evaluation" / "retrieval" / "cases" / "retrieval_cases.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "evaluation" / "retrieval" / "reports"
DEFAULT_EXPERIMENTS = PROJECT_ROOT / "evaluation" / "retrieval" / "experiments.jsonl"
DEFAULT_KS = (1, 3, 5, 10, 20)

Retriever = Callable[[str, int], list[dict[str, Any]]]


def retrieve_bm25_base(query: str, top_k: int, corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> list[dict[str, Any]]:
    return retrieve_by_bm25(query, top_k=top_k, metadata_mode="base", corpus_dir=corpus_dir)


def retrieve_bm25_metadata(query: str, top_k: int, corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> list[dict[str, Any]]:
    return retrieve_by_bm25(query, top_k=top_k, metadata_mode="unweighted", corpus_dir=corpus_dir)


def retrieve_metadata_embedding(query: str, top_k: int, index_dir: Path = SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR) -> list[dict[str, Any]]:
    return retrieve_by_embedding(
        query,
        top_k=top_k,
        index_dir=index_dir,
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


def make_methods(
    corpus_dir: Path,
    index_dir: Path,
    bm25_metadata_mode: str,
) -> dict[str, Retriever]:
    def bm25(query: str, top_k: int) -> list[dict[str, Any]]:
        return retrieve_by_bm25(query, top_k=top_k, metadata_mode=bm25_metadata_mode, corpus_dir=corpus_dir)

    def bm25_semantic_metadata(query: str, top_k: int) -> list[dict[str, Any]]:
        return retrieve_by_bm25(query, top_k=top_k, metadata_mode="unweighted", corpus_dir=corpus_dir)

    def keyword(query: str, top_k: int) -> list[dict[str, Any]]:
        return retrieve_by_keyword_baseline(query, top_k=top_k, corpus_dir=corpus_dir)

    def embedding(query: str, top_k: int) -> list[dict[str, Any]]:
        return retrieve_by_embedding(query, top_k=top_k, index_dir=index_dir)

    def hybrid(query: str, top_k: int) -> list[dict[str, Any]]:
        return hybrid_retrieve(
            query,
            hybrid_top_k=top_k,
            corpus_dir=corpus_dir,
            embedding_index_dir=index_dir,
            bm25_metadata_mode=bm25_metadata_mode,
        )

    def rrf(query: str, top_k: int) -> list[dict[str, Any]]:
        return hybrid_retrieve_rrf(
            query,
            top_k=top_k,
            corpus_dir=corpus_dir,
            embedding_index_dir=index_dir,
            bm25_metadata_mode=bm25_metadata_mode,
        )

    return {
        "keyword": keyword,
        "bm25": bm25,
        "bm25_semantic_metadata": bm25_semantic_metadata,
        "embedding": embedding,
        "metadata_embedding": lambda query, top_k: retrieve_metadata_embedding(query, top_k),
        "linear_hybrid": hybrid,
        "rrf_hybrid": rrf,
    }


def load_cases(path: Path) -> list[dict[str, Any]]:
    return load_cases_with_evidence(path, expected_count=48)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def ndcg(covered_by_rank: list[set[int]], evidence_count: int, k: int) -> float:
    newly_covered: set[int] = set()
    gains: list[float] = []
    for covered in covered_by_rank[:k]:
        new_evidence = covered - newly_covered
        gains.append(1.0 if new_evidence else 0.0)
        newly_covered.update(covered)
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal_count = min(evidence_count, k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / idcg if idcg else 0.0


def metrics_for(
    relevant: list[bool],
    covered_by_rank: list[set[int]],
    evidence_count: int,
    ks: tuple[int, ...],
) -> dict[str, float]:
    """Existing benchmark metric formulas, fed by relevance-layer output."""
    metrics: dict[str, float] = {}
    for k in ks:
        covered = len(covered_by_rank[k - 1]) if covered_by_rank and k <= len(covered_by_rank) else 0
        metrics[f"hit@{k}"] = float(any(relevant[:k]))
        metrics[f"recall@{k}"] = covered / evidence_count if evidence_count else 0.0
        metrics[f"precision@{k}"] = sum(relevant[:k]) / k if k else 0.0
        metrics[f"nDCG@{k}"] = ndcg(covered_by_rank, evidence_count, k)
    first_relevant = next((rank for rank, value in enumerate(relevant, 1) if value), 0)
    metrics["mrr@5"] = 1.0 / first_relevant if 0 < first_relevant <= 5 else 0.0
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
    gold_evidence = [str(evidence) for evidence in case["gold_evidence"]]
    started = time.perf_counter()
    results = retriever(str(case["query"]), top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    chunks = [serializable_chunk(item, rank, method) for rank, item in enumerate(results[:top_k], 1)]
    retrieved_sources = [chunk["source"] for chunk in chunks]
    relevant, covered_by_rank = relevance_for(results[:top_k], gold_evidence)
    return {
        "case_id": str(case["id"]),
        "topic": case.get("topic", ""),
        "query_type": case.get("query_type", ""),
        "difficulty": case.get("difficulty", ""),
        "query": str(case["query"]),
        "gold_evidence": gold_evidence,
        "retrieved_sources": retrieved_sources,
        "metrics": metrics_for(relevant, covered_by_rank, len(gold_evidence), ks),
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


def method_config(
    method: str,
    top_k: int,
    ks: tuple[int, ...],
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
    index_dir: Path = BASE_VECTOR_INDEX_DIR,
    bm25_metadata_mode: str = "base",
) -> dict[str, Any]:
    config: dict[str, Any] = {"top_k": top_k, "ks": list(ks)}
    if method == "keyword":
        config["retriever"] = "keyword baseline"
    elif method == "bm25":
        config.update({"metadata_mode": bm25_metadata_mode, "corpus_dir": str(corpus_dir)})
    elif method == "bm25_semantic_metadata":
        config.update({"metadata_mode": "unweighted", "corpus_dir": str(corpus_dir)})
    elif method == "embedding":
        config.update({"index_dir": str(index_dir), "embedding_model": get_embedding_model_name()})
    elif method == "metadata_embedding":
        config.update({"index_dir": str(index_dir), "embedding_model": get_embedding_model_name()})
    elif method == "linear_hybrid":
        config.update({
            "keyword_weight": KEYWORD_WEIGHT,
            "embedding_weight": EMBEDDING_WEIGHT,
            "candidate_k": max(top_k * CANDIDATE_MULTIPLIER, MIN_CANDIDATES),
            "corpus_dir": str(corpus_dir),
            "index_dir": str(index_dir),
            "bm25_metadata_mode": bm25_metadata_mode,
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
    parser.add_argument("--corpus-dir", type=Path, default=PRIVATE_KNOWLEDGE_DIR)
    parser.add_argument("--index-dir", type=Path, default=BASE_VECTOR_INDEX_DIR)
    parser.add_argument("--bm25-metadata-mode", choices=("base", "unweighted", "weighted"), default="base")
    parser.add_argument("--methods", nargs="+", choices=tuple(METHODS), default=list(METHODS))
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")

    ks = tuple(k for k in DEFAULT_KS if k <= args.top_k)
    if args.top_k not in ks:
        ks += (args.top_k,)
    cases = load_cases(args.cases)
    methods = make_methods(args.corpus_dir, args.index_dir, args.bm25_metadata_mode)
    reset_retrieval_caches()

    started = time.perf_counter()
    strategies: dict[str, Any] = {}
    for method in args.methods:
        evaluated = [
            evaluate_case(case, methods[method], method, args.top_k, ks)
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
                "config": method_config(method, args.top_k, ks, args.corpus_dir, args.index_dir, args.bm25_metadata_mode),
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
