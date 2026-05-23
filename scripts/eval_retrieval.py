from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.retrieval.embedding_retriever import retrieve_by_embedding
from app.rag.retrieval.hybrid_retriever import (
    CANDIDATE_MULTIPLIER,
    EMBEDDING_WEIGHT,
    KEYWORD_WEIGHT,
    MIN_CANDIDATES,
)
from app.rag.retrieval.hybrid_retriever import hybrid_retrieve
from app.rag.retrieval.hybrid_retriever_rrf import (
    RRF_CANDIDATE_MULTIPLIER,
    RRF_K,
    RRF_MIN_CANDIDATES,
    hybrid_retrieve_rrf,
)
from app.rag.retrieval.keyword_retriever import retrieve_by_keyword


DEFAULT_CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_cases.json"
DEFAULT_EXPERIMENTS_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_experiments.jsonl"
DEFAULT_EXPERIMENTS_MD_PATH = PROJECT_ROOT / "tests" / "evals" / "retrieval_experiments.md"
Retriever = Callable[[str, int], list[dict[str, Any]]]


@dataclass
class CaseResult:
    case_id: str
    topic: str
    query: str
    expected_sources: list[str]
    retrieved_sources: list[str]
    hit_at_3: float
    hit_at_5: float
    recall_at_5: float
    mrr_at_5: float


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_key(item: dict[str, Any]) -> str:
    return str(item.get("source", ""))


def evaluate_case(case: dict[str, Any], retriever: Retriever, top_k: int) -> CaseResult:
    expected_sources = list(dict.fromkeys(case["expected_sources"]))
    expected = set(expected_sources)
    results = retriever(case["query"], top_k)
    retrieved_sources = [source_key(item) for item in results]

    top_3 = retrieved_sources[:3]
    top_5 = retrieved_sources[:5]
    top_5_hits = [source for source in top_5 if source in expected]

    first_rank = 0
    for rank, source in enumerate(top_5, start=1):
        if source in expected:
            first_rank = rank
            break

    return CaseResult(
        case_id=case["id"],
        topic=case.get("topic", ""),
        query=case["query"],
        expected_sources=expected_sources,
        retrieved_sources=retrieved_sources,
        hit_at_3=1.0 if any(source in expected for source in top_3) else 0.0,
        hit_at_5=1.0 if top_5_hits else 0.0,
        recall_at_5=len(set(top_5_hits)) / len(expected) if expected else 0.0,
        mrr_at_5=1.0 / first_rank if first_rank else 0.0,
    )


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(results: list[CaseResult]) -> dict[str, float]:
    return {
        "cases": float(len(results)),
        "hit@3": average([result.hit_at_3 for result in results]),
        "hit@5": average([result.hit_at_5 for result in results]),
        "recall@5": average([result.recall_at_5 for result in results]),
        "mrr@5": average([result.mrr_at_5 for result in results]),
    }


def print_summary(all_results: dict[str, list[CaseResult]]) -> None:
    print("| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for method, results in all_results.items():
        summary = summarize(results)
        print(
            f"| {method} | {int(summary['cases'])} | "
            f"{summary['hit@3']:.3f} | {summary['hit@5']:.3f} | "
            f"{summary['recall@5']:.3f} | {summary['mrr@5']:.3f} |"
        )


def print_failures(all_results: dict[str, list[CaseResult]]) -> None:
    for method, results in all_results.items():
        failures = [result for result in results if result.hit_at_5 == 0]
        if not failures:
            continue

        print(f"\n## {method} failed cases")
        for result in failures:
            print(f"\n- {result.case_id} ({result.topic})")
            print(f"  query: {result.query}")
            print(f"  expected: {', '.join(result.expected_sources)}")
            print(f"  retrieved: {', '.join(result.retrieved_sources[:5])}")


def build_experiment_record(
    experiment_name: str,
    cases_path: Path,
    top_k: int,
    all_results: dict[str, list[CaseResult]],
    notes: str,
) -> dict[str, Any]:
    return {
        "experiment": experiment_name,
        "cases_path": str(cases_path),
        "case_count": len(next(iter(all_results.values()), [])),
        "top_k": top_k,
        "parameters": {
            "keyword_weight": KEYWORD_WEIGHT,
            "embedding_weight": EMBEDDING_WEIGHT,
            "candidate_multiplier": CANDIDATE_MULTIPLIER,
            "min_candidates": MIN_CANDIDATES,
            "rrf_k": RRF_K,
            "rrf_candidate_multiplier": RRF_CANDIDATE_MULTIPLIER,
            "rrf_min_candidates": RRF_MIN_CANDIDATES,
        },
        "metrics": {
            method: summarize(results)
            for method, results in all_results.items()
        },
        "notes": notes,
    }


def append_experiment(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_experiment_markdown(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    existing_text = path.read_text(encoding="utf-8") if path.exists() else ""

    if not existing_text.strip():
        lines.extend(["# Retrieval Experiments", ""])
    elif not existing_text.endswith("\n\n"):
        lines.append("")

    lines.extend(
        [
            f"## {record['experiment']}",
            "",
            f"- cases: {record['case_count']}",
            f"- top_k: {record['top_k']}",
            f"- keyword_weight: {record['parameters']['keyword_weight']}",
            f"- embedding_weight: {record['parameters']['embedding_weight']}",
            f"- candidate_multiplier: {record['parameters']['candidate_multiplier']}",
            f"- min_candidates: {record['parameters']['min_candidates']}",
            f"- rrf_k: {record['parameters']['rrf_k']}",
            f"- rrf_candidate_multiplier: {record['parameters']['rrf_candidate_multiplier']}",
            f"- rrf_min_candidates: {record['parameters']['rrf_min_candidates']}",
            f"- notes: {record['notes'] or '-'}",
            "",
            "| method | cases | hit@3 | hit@5 | recall@5 | mrr@5 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for method, metrics in record["metrics"].items():
        lines.append(
            f"| {method} | {int(metrics['cases'])} | "
            f"{metrics['hit@3']:.3f} | {metrics['hit@5']:.3f} | "
            f"{metrics['recall@5']:.3f} | {metrics['mrr@5']:.3f} |"
        )

    lines.append("")

    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate keyword, embedding, and hybrid retrieval.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--record-experiment", action="store_true")
    parser.add_argument("--no-jsonl-record", action="store_true")
    parser.add_argument("--experiment-name", default="manual_eval")
    parser.add_argument("--experiments-out", type=Path, default=DEFAULT_EXPERIMENTS_PATH)
    parser.add_argument("--experiments-md-out", type=Path, default=DEFAULT_EXPERIMENTS_MD_PATH)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--method",
        choices=["keyword", "embedding", "hybrid", "hybrid_rrf", "all"],
        default="all",
    )
    args = parser.parse_args()

    retrievers: dict[str, Retriever] = {
        "keyword": retrieve_by_keyword,
        "embedding": retrieve_by_embedding,
        "hybrid": hybrid_retrieve,
        "hybrid_rrf": hybrid_retrieve_rrf,
    }
    if args.method != "all":
        retrievers = {args.method: retrievers[args.method]}

    cases = load_cases(args.cases)
    all_results = {
        method: [
            evaluate_case(case, retriever, top_k=args.top_k)
            for case in cases
        ]
        for method, retriever in retrievers.items()
    }

    print_summary(all_results)
    print_failures(all_results)

    if args.record_experiment:
        record = build_experiment_record(
            experiment_name=args.experiment_name,
            cases_path=args.cases,
            top_k=args.top_k,
            all_results=all_results,
            notes=args.notes,
        )
        if not args.no_jsonl_record:
            append_experiment(args.experiments_out, record)
        append_experiment_markdown(args.experiments_md_out, record)
        if not args.no_jsonl_record:
            print(f"experiment_recorded: {args.experiments_out}")
        print(f"experiment_markdown_recorded: {args.experiments_md_out}")


if __name__ == "__main__":
    main()
