from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.retrievers.embedding import get_cached_vector_index, retrieve_by_embedding
from app.tools.retrieval.retrievers.bm25 import (
    clear_bm25_caches,
    get_cached_bm25_index,
    load_semantic_metadata_by_source,
    load_semantic_metadata_by_source_unweighted,
    retrieve_by_bm25,
)
from scripts.eval_retrieval import STRATEGIES, atomic_write_json, evaluate_case as _old_case, strategy_config

CASES = PROJECT_ROOT / "tests/evals/retrieval_cases_v2.json"
SPLIT = PROJECT_ROOT / "tests/evals/retrieval_cases_v2_split.json"
REPORT = PROJECT_ROOT / "tests/evals/reports/retrieval_eval_report_v2_unweighted_baseline.json"
EXPERIMENTS = PROJECT_ROOT / "tests/evals/retrieval_experiments.jsonl"


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def ndcg(retrieved: list[str], expected: set[str], k: int) -> float:
    gains = [1.0 if source in expected else 0.0 for source in retrieved[:k]]
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = min(len(expected), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal + 1))
    return dcg / idcg if idcg else 0.0


def case_result(case: dict[str, Any], retriever: Any, method: str) -> dict[str, Any]:
    expected_sources = list(dict.fromkeys(str(s) for s in case["expected_sources"]))
    expected = set(expected_sources)
    started = time.perf_counter()
    results = retriever(str(case["query"]), 20)
    elapsed = (time.perf_counter() - started) * 1000.0
    chunks = []
    for rank, item in enumerate(results[:20], 1):
        chunk = {"source": str(item.get("source", "")), "rank": rank, "retrieval_method": item.get("retrieval_method", method)}
        for key in ("embedding_cosine_score", "embedding_score", "bm25_score", "keyword_score", "normalized_bm25_score", "normalized_embedding_cosine_score", "hybrid_score", "keyword_rank", "embedding_rank", "rrf_score"):
            if key in item:
                chunk[key] = item[key]
        chunks.append(chunk)
    retrieved = [c["source"] for c in chunks]
    metrics: dict[str, float] = {}
    for k in (1, 3, 5, 10):
        metrics[f"hit@{k}"] = float(any(s in expected for s in retrieved[:k]))
    for k in (5, 10, 20):
        metrics[f"recall@{k}"] = len({s for s in retrieved[:k] if s in expected}) / len(expected) if expected else 0.0
    first = next((rank for rank, source in enumerate(retrieved[:5], 1) if source in expected), 0)
    metrics["mrr@5"] = 1.0 / first if first else 0.0
    metrics["precision@5"] = len({s for s in retrieved[:5] if s in expected}) / 5.0
    metrics["nDCG@5"] = ndcg(retrieved, expected, 5)
    metrics["nDCG@10"] = ndcg(retrieved, expected, 10)
    return {
        "case_id": str(case["id"]), "split": case["split"], "topic": case["topic"],
        "query_type": case.get("query_type", ""), "difficulty": case.get("difficulty", ""),
        "query": case["query"], "expected_sources": expected_sources,
        "retrieved_sources": retrieved, "top_k_chunks": chunks, "metrics": metrics,
        "retrieval_time_ms": elapsed,
    }


def summary(cases: list[dict[str, Any]]) -> dict[str, float]:
    keys = ["hit@1", "hit@3", "hit@5", "hit@10", "recall@5", "recall@10", "recall@20", "mrr@5", "precision@5", "nDCG@5", "nDCG@10"]
    return {"cases": len(cases), **{key: mean([c["metrics"][key] for c in cases]) for key in keys}}


def grouped(cases: list[dict[str, Any]], field: str) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        buckets[str(case[field])].append(case)
    return {key: summary(value) for key, value in sorted(buckets.items())}


def candidate_coverage(cases: list[dict[str, Any]], final_results: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Measure candidate recall before ranking, plus final hybrid ranks."""
    dev_cases = [case for case in cases if case["split"] == "dev"]
    per_case = []
    for case in dev_cases:
        expected = set(case["expected_sources"])
        bm25 = retrieve_by_bm25(case["query"], top_k=50)
        embedding = retrieve_by_embedding(case["query"], top_k=50)
        bm25_sources = [str(item["source"]) for item in bm25]
        embedding_sources = [str(item["source"]) for item in embedding]
        union_sources = sorted(set(bm25_sources) | set(embedding_sources), key=lambda source: min(
            bm25_sources.index(source) + 1 if source in bm25_sources else 10**9,
            embedding_sources.index(source) + 1 if source in embedding_sources else 10**9,
        ))
        ranks = lambda sources: {source: (sources.index(source) + 1 if source in sources else None) for source in expected}
        final_ranks = {}
        for method in ("linear_hybrid", "rrf_hybrid"):
            sources = [str(item["source"]) for item in final_results[method][case["id"]]]
            final_ranks[method] = ranks(sources)
        per_case.append({
            "case_id": case["id"], "topic": case["topic"], "query_type": case.get("query_type", ""), "difficulty": case.get("difficulty", ""),
            "query": case["query"], "expected_sources": sorted(expected),
            "bm25_top50": [{"source": str(item["source"]), "rank": rank, "score": item.get("bm25_score", item.get("keyword_score"))} for rank, item in enumerate(bm25, 1)],
            "embedding_top50": [{"source": str(item["source"]), "rank": rank, "score": item.get("embedding_cosine_score", item.get("embedding_score"))} for rank, item in enumerate(embedding, 1)],
            "expected_ranks": {"bm25_top50": ranks(bm25_sources), "embedding_top50": ranks(embedding_sources), "candidate_union_top50": ranks(union_sources), "linear_hybrid_final_top20": final_ranks["linear_hybrid"], "rrf_hybrid_final_top20": final_ranks["rrf_hybrid"]},
            "candidate_recall@20": {"bm25": len(expected & set(bm25_sources[:20])) / len(expected), "embedding": len(expected & set(embedding_sources[:20])) / len(expected), "union": len(expected & (set(bm25_sources[:20]) | set(embedding_sources[:20]))) / len(expected)},
            "candidate_recall@50": {"bm25": len(expected & set(bm25_sources[:50])) / len(expected), "embedding": len(expected & set(embedding_sources[:50])) / len(expected), "union": len(expected & (set(bm25_sources[:50]) | set(embedding_sources[:50]))) / len(expected)},
        })
    return {
        "scope": "dev",
        "cases": per_case,
        "summary": {"cases": len(per_case), "recall@20": {name: mean([c["candidate_recall@20"][name] for c in per_case]) for name in ("bm25", "embedding", "union")}, "recall@50": {name: mean([c["candidate_recall@50"][name] for c in per_case]) for name in ("bm25", "embedding", "union")}},
        "focus_cases": {case_id: next(c for c in per_case if c["case_id"] == case_id) for case_id in ("metrics_005", "self_drive_005", "self_drive_006")},
    }


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assignments = split["assignments"]
    for case in cases:
        case["split"] = assignments[case["id"]]
    if len(cases) != 48 or sum(c["split"] == "regression" for c in cases) != 16 or sum(c["split"] == "dev" for c in cases) != 24 or sum(c["split"] == "test" for c in cases) != 8:
        raise ValueError("Invalid fixed split counts")
    clear_bm25_caches()
    get_cached_vector_index.cache_clear()
    results: dict[str, Any] = {"schema_version": "retrieval_eval_v2", "cases_path": str(CASES), "top_k": 20, "split": split, "strategies": {}}
    final_results: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for method, retriever in STRATEGIES.items():
        evaluated = [case_result(case, retriever, method) for case in cases]
        final_results[method] = {case["case_id"]: [{"source": chunk["source"], "rank": chunk["rank"]} for chunk in case["top_k_chunks"]] for case in evaluated}
        results["strategies"][method] = {
            "config": strategy_config(method, 20), "overall": summary(evaluated),
            "regression": summary([c for c in evaluated if c["split"] == "regression"]),
            "dev": summary([c for c in evaluated if c["split"] == "dev"]),
            "test": summary([c for c in evaluated if c["split"] == "test"]),
            "by_topic": grouped(evaluated, "topic"), "by_query_type": grouped(evaluated, "query_type"),
            "by_difficulty": grouped(evaluated, "difficulty"), "cases": evaluated,
        }
    results["candidate_coverage"] = candidate_coverage(cases, final_results)
    atomic_write_json(REPORT, results)
    record = {"experiment":"retrieval_eval_v2_unweighted_candidate_coverage","timestamp_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"cases":str(CASES),"report":str(REPORT),"top_k":20,"candidate_top_k":50,"split_scheme":split["scheme"],"bm25_metadata_mode":"unweighted","metadata_repetition":"once_per_field","strategies":{k:v["overall"] for k,v in results["strategies"].items()},"candidate_coverage_summary":results["candidate_coverage"]["summary"]}
    EXPERIMENTS.parent.mkdir(parents=True, exist_ok=True)
    with EXPERIMENTS.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    keys = ["hit@1","hit@3","hit@5","hit@10","recall@5","recall@10","recall@20","mrr@5","precision@5","nDCG@5","nDCG@10"]
    print("| strategy | " + " | ".join(keys) + " |")
    print("|---|" + "---:|" * len(keys))
    for method, value in results["strategies"].items():
        print("| " + method + " | " + " | ".join(f"{value['overall'][k]:.3f}" for k in keys) + " |")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
