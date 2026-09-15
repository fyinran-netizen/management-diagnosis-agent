"""Orchestrate DeepEval over saved generation benchmark output only."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from deepeval.test_case import LLMTestCase  # noqa: E402

from evaluation.generation.evaluation.metrics.answer_relevancy import (  # noqa: E402
    build_metric as build_answer_relevancy,
)
from evaluation.generation.evaluation.metrics.diagnosis_quality import (  # noqa: E402
    build_metric as build_diagnosis_quality,
)
from evaluation.generation.evaluation.metrics.faithfulness import (  # noqa: E402
    build_metric as build_faithfulness,
)
from evaluation.generation.evaluation.ollama_deepeval_model import (  # noqa: E402
    OllamaDeepEvalModel,
)
from app.core.config import GENERATION_MODEL, OLLAMA_BASE_URL, GENERATION_EVALUATION_MODEL  # noqa: E402


DEFAULT_INPUT = PROJECT_ROOT / "evaluation" / "generation" / "generation_benchmark.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "evaluation" / "generation" / "reports"
METRIC_NAMES = ("faithfulness", "answer_relevancy", "diagnosis_quality")


def load_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    cases = report.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"Generation benchmark must contain a non-empty cases list: {path}")
    return report


def load_case_ids(path: Path) -> list[str]:
    case_ids = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(case_ids, list) or not case_ids:
        raise ValueError(f"Case ID file must contain a non-empty JSON list: {path}")
    if not all(isinstance(case_id, str) and case_id.strip() for case_id in case_ids):
        raise ValueError(f"Case ID file must contain only non-empty strings: {path}")
    return [case_id.strip() for case_id in case_ids]


def build_metrics(model: OllamaDeepEvalModel) -> dict[str, Any]:
    return {
        "faithfulness": build_faithfulness(model),
        "answer_relevancy": build_answer_relevancy(model),
        "diagnosis_quality": build_diagnosis_quality(model),
    }


def evaluate_case(case: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    chunks = case.get("retrieved_top5_chunks")
    if not isinstance(chunks, list) or len(chunks) != 5:
        raise ValueError(f"Case {case.get('case_id')!r} must contain exactly 5 retrieved chunks")
    retrieval_context = []
    for index, chunk in enumerate(chunks, start=1):
        if not isinstance(chunk, dict) or not isinstance(chunk.get("content"), str):
            raise ValueError(f"Case {case.get('case_id')!r} chunk {index} has no content")
        retrieval_context.append(chunk["content"])

    test_case = LLMTestCase(
        input=str(case["query"]),
        actual_output=str(case["generated_report"]),
        retrieval_context=retrieval_context,
    )
    result: dict[str, Any] = {"score": {}, "reason": {}}
    for name, metric in metrics.items():
        result["score"][name] = float(metric.measure(test_case, _show_indicator=False))
        result["reason"][name] = getattr(metric, "reason", None)
    return result


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "mean": statistics.fmean(float(case["metrics"]["score"][name]) for case in cases),
            "median": statistics.median(float(case["metrics"]["score"][name]) for case in cases),
            "min": min(float(case["metrics"]["score"][name]) for case in cases),
            "max": max(float(case["metrics"]["score"][name]) for case in cases),
            "count": len(cases),
        }
        for name in METRIC_NAMES
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    case = report["cases"][0]
    lines = [
        "# Generation Evaluation", "",
        f"- Case: `{case['case_id']}`",
        f"- Input benchmark: `{report['input_path']}`",
        f"- Judge model: `{report['judge']['model']}`",
        f"- Ollama base URL: `{report['judge']['ollama_base_url']}`", "",
        "## Scores", "",
        "| Metric | Score | Reason |", "| --- | ---: | --- |",
    ]
    for name in METRIC_NAMES:
        score = case["metrics"]["score"][name]
        reason = str(case["metrics"]["reason"].get(name) or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {name} | {score:.3f} | {reason} |")
    lines.extend(["", "The JSON report contains the evaluated case and its metric details.", "",])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate saved generation output with DeepEval.")
    case_selection = parser.add_mutually_exclusive_group()
    case_selection.add_argument("--case-id", help="Evaluate only this case ID.")
    case_selection.add_argument(
        "--case-ids-file",
        type=Path,
        help="Evaluate the case IDs listed in this JSON array file.",
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    source = load_report(args.input)
    cases = source["cases"]
    if args.case_id:
        cases = [case for case in cases if str(case.get("case_id")) == args.case_id]
        if not cases:
            raise ValueError(f"Case ID not found: {args.case_id}")
    elif args.case_ids_file:
        requested_ids = load_case_ids(args.case_ids_file)
        cases_by_id = {str(case.get("case_id")): case for case in cases}
        missing_ids = [case_id for case_id in requested_ids if case_id not in cases_by_id]
        if missing_ids:
            raise ValueError(
                f"Case IDs not found in generation benchmark: {', '.join(missing_ids)}"
            )
        cases = [cases_by_id[case_id] for case_id in requested_ids]

    model = OllamaDeepEvalModel()
    metrics = build_metrics(model)
    started = time.perf_counter()
    evaluated_cases = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        evaluated = {
            "case_id": str(case["case_id"]),
            "query": str(case["query"]),
            "metrics": evaluate_case(case, metrics),
        }
        evaluated_cases.append(evaluated)
        report = {
            "schema_version": "generation_deepeval_evaluation_v1",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "input_path": str(args.input), "case_count": 1,
            "judge": {"provider": "ollama", "model": GENERATION_EVALUATION_MODEL, "ollama_base_url": OLLAMA_BASE_URL},
            "metrics": list(METRIC_NAMES), "elapsed_seconds": time.perf_counter() - started,
            "summary": summarize([evaluated]), "cases": [evaluated],
        }
        json_path = args.output_dir / f"{evaluated['case_id']}.json"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_markdown(report, json_path.with_suffix(".md"))
        print(f"json: {json_path}")
        print(f"markdown: {json_path.with_suffix('.md')}")


if __name__ == "__main__":
    main()
