from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import (  # noqa: E402
    GENERATION_MODEL,
    OLLAMA_BASE_URL,
)
from app.tools.generation import generate_report  # noqa: E402
from app.core.config import PRIVATE_KNOWLEDGE_DIR  # noqa: E402
from app.tools.retrieval.knowledge_loader import (  # noqa: E402
    iter_markdown_files,
    load_chunks_from_path,
)

TOP_K = 5
DEFAULT_CASES = PROJECT_ROOT / "evaluation" / "retrieval" / "cases" / "retrieval_cases.json"
DEFAULT_BASELINE_DIR = PROJECT_ROOT / "evaluation" / "understanding" / "best_retrieval_baseline"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "generation" / "generation_benchmark.json"
GOAL = "识别主要管理问题，分析可能的根本原因，并提出可执行的下一步建议。"
REQUIRED_CHUNK_FIELDS = ("chapter_title", "section_title", "title", "content")


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        raise ValueError(f"Cases file must contain a JSON list of objects: {path}")
    if len(cases) != 48:
        raise ValueError(f"Expected 48 retrieval cases, found {len(cases)} in {path}")
    return cases


def find_baseline(path: Path | None) -> Path:
    if path is not None:
        return path
    reports = sorted(DEFAULT_BASELINE_DIR.glob("understanding_benchmark_*.json"))
    if not reports:
        raise FileNotFoundError(f"No understanding baseline report found in {DEFAULT_BASELINE_DIR}")
    return reports[-1]


def load_raw_top5(path: Path) -> dict[str, list[dict[str, Any]]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    try:
        raw_cases = report["strategies"]["raw"]["cases"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Baseline does not contain strategies.raw.cases: {path}") from exc
    if len(raw_cases) != 48:
        raise ValueError(f"Expected 48 raw baseline cases, found {len(raw_cases)} in {path}")

    result: dict[str, list[dict[str, Any]]] = {}
    for case in raw_cases:
        case_id = str(case.get("case_id", ""))
        chunks = case.get("top_k_chunks")
        if not case_id or not isinstance(chunks, list) or len(chunks) < TOP_K:
            raise ValueError(f"Invalid raw Top5 result for case {case_id!r} in {path}")
        if case_id in result:
            raise ValueError(f"Duplicate case_id in raw baseline: {case_id}")
        result[case_id] = chunks[:TOP_K]
    return result


def build_chunk_index() -> dict[str, dict[str, Any]]:
    # Only load the private knowledge base used by the retrieval benchmark.
    chunks = []

    for path in iter_markdown_files(
        PRIVATE_KNOWLEDGE_DIR,
        recursive=True,
        skipped_top_level_dirs={"ch00"},
    ):
        chunks.extend(
            load_chunks_from_path(
                path,
                PRIVATE_KNOWLEDGE_DIR,
            )
        )
    by_source: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        item = {
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "chapter_title": chunk.chapter_title,
            "section_title": chunk.section_title,
            "title": chunk.title,
            "content": chunk.content,
        }
        by_source.setdefault(chunk.source, []).append(item)

    duplicates = {source: items for source, items in by_source.items() if len(items) != 1}
    if duplicates:
        details = ", ".join(f"{source} ({len(items)})" for source, items in duplicates.items())
        raise ValueError(f"Knowledge source is not unique: {details}")
    return {source: items[0] for source, items in by_source.items()}


def restore_top5(
    raw_chunks: list[dict[str, Any]],
    chunk_index: dict[str, dict[str, Any]],
    case_id: str,
) -> list[dict[str, Any]]:
    restored: list[dict[str, Any]] = []
    for expected_rank, raw in enumerate(raw_chunks, start=1):
        source = str(raw.get("source", ""))
        if not source:
            raise ValueError(f"Case {case_id}: raw Top5 item {expected_rank} has no source")
        if source not in chunk_index:
            raise ValueError(f"Case {case_id}: cannot uniquely restore source {source!r}")
        item = chunk_index[source]
        if any(item.get(field) in (None, "") for field in REQUIRED_CHUNK_FIELDS):
            raise ValueError(f"Case {case_id}: restored source {source!r} is missing a required field")
        restored.append(
            {
                "rank": expected_rank,
                "source": source,
                "chunk_index": item["chunk_index"],
                "chapter_title": item["chapter_title"],
                "section_title": item["section_title"],
                "title": item["title"],
                "content": item["content"],
            }
        )
    return restored


def write_markdown(report: dict[str, Any], path: Path) -> None:
    completed = len(report["cases"])
    lines = [
        "# Generation Benchmark",
        "",
        f"- Cases completed: `{completed}/{report['case_count']}`",
        f"- Top K: `{report['top_k']}`",
        f"- Raw retrieval baseline: `{report['baseline_path']}`",
        f"- Generation model: `{report['generation']['model']}`",
        f"- Generation mode: `{report['generation']['mode']}`",
        "",
        "This benchmark uses the saved raw Top5 retrieval results and does not rerun Understanding or Retrieval.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, output.with_suffix(".md"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate initial generation on the saved raw retrieval baseline.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cases = load_cases(args.cases)
    baseline_path = find_baseline(args.baseline)
    raw_top5 = load_raw_top5(baseline_path)
    knowledge = build_chunk_index()
    case_by_id = {str(case["id"]): case for case in cases}
    if set(raw_top5) != set(case_by_id):
        raise ValueError("Raw baseline case IDs do not exactly match the 48 retrieval cases")

    report: dict[str, Any] = {
        "schema_version": "generation_initial_best_retrieval_baseline_v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases_path": str(args.cases),
        "baseline_path": str(baseline_path),
        "case_count": len(cases),
        "top_k": TOP_K,
        "retrieval": {"strategy": "raw", "rerun": False, "baseline_top_k": TOP_K},
        "understanding": {"rerun": False},
        "generation": {
            "mode": "initial",
            "validation_revision_loop": False,
            "model": GENERATION_MODEL,
            "ollama_base_url": OLLAMA_BASE_URL,
            "knowledge_include_private": True,
            "problem_types": [],
            "diagnosis_hints": [],
            "diagnosis_summary": {},
        },
        "cases": [],
    }

    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if existing.get("baseline_path") == str(baseline_path) and existing.get("top_k") == TOP_K:
            report["cases"] = existing.get("cases", [])
    completed = {str(case["case_id"]): case for case in report["cases"]}

    for case in cases:
        case_id = str(case["id"])
        if case_id in completed and completed[case_id].get("generated_report"):
            continue
        retrieved = restore_top5(raw_top5[case_id], knowledge, case_id)
        started = time.perf_counter()
        generated = generate_report(
            company_context=str(case["query"]),
            goal=GOAL,
            language="zh",
            retrieved_chunks=retrieved,
            problem_types=[],
            diagnosis_hints=[],
            diagnosis_summary={},
        )
        result = {
            "case_id": case_id,
            "query": str(case["query"]),
            "retrieved_top5_chunks": retrieved,
            "generated_report": generated,
            "generation_time": (time.perf_counter() - started),
            "generation_model_config": report["generation"],
        }
        completed[case_id] = result
        report["cases"] = [completed[str(item["id"])] for item in cases if str(item["id"]) in completed]
        save_report(report, args.output)
        print(f"completed {case_id} ({len(report['cases'])}/{len(cases)})")

    save_report(report, args.output)
    print(f"json: {args.output}")
    print(f"markdown: {args.output.with_suffix('.md')}")


if __name__ == "__main__":
    main()
