"""Extract selected final Top 10 reranking benchmark cases into Markdown.

This script only reads an existing benchmark JSON report. It does not run
retrieval or reranking and does not modify any retrieval-related logic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CASE_IDS = [
    "customer_value_002",
    "sales_marketing_005",
    "opportunity_005",
    "strategy_org_003",
    "metrics_004",
    "self_drive_001",
    "long_term_decision_005",
    "entrepreneurship_001",
]

METRIC_KEYS = [
    "hit@1",
    "hit@3",
    "hit@5",
    "recall@5",
    "recall@10",
    "mrr@5",
    "nDCG@5",
    "nDCG@10",
    "precision@5",
]


def fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def rank_map(items: list[dict[str, Any]]) -> dict[str, int]:
    return {item["source"]: item["rank"] for item in items}


def render_top10(label: str, result: dict[str, Any]) -> list[str]:
    lines = [f"#### {label} Top 10", "", "| Rank | Source | Title | Score | Rerank score |", "|---:|---|---|---:|---:|"]
    for item in result["top_k_chunks"][:10]:
        lines.append(
            "| {rank} | `{source}` | {title} | {score} | {rerank} |".format(
                rank=item.get("rank", "—"),
                source=cell(item.get("source", "—")),
                title=cell(item.get("title", "—")),
                score=fmt(item.get("score")),
                rerank=fmt(item.get("rerank_score")),
            )
        )
    return lines


def render_case(case_id: str, baseline: dict[str, Any], rerank: dict[str, Any]) -> list[str]:
    gold_evidence = baseline.get("gold_evidence", [])
    base_items = baseline["top_k_chunks"][:10]
    rerank_items = rerank["top_k_chunks"][:10]
    base_ranks = rank_map(base_items)
    rerank_ranks = rank_map(rerank_items)

    lines = [f"## {case_id}", "", "### 基本信息和 query", ""]
    lines += [
        "| Field | Value |",
        "|---|---|",
        f"| Topic | `{cell(baseline.get('topic', '—'))}` |",
        f"| Query type | `{cell(baseline.get('query_type', '—'))}` |",
        f"| Difficulty | `{cell(baseline.get('difficulty', '—'))}` |",
        f"| Query | {cell(baseline.get('query', '—'))} |",
        "",
        "### Gold evidence",
        "",
        "<br>".join(cell(evidence) for evidence in gold_evidence),
        "",
        "### 主要 metrics（final Top 10）",
        "",
        "| Metric | Baseline | Rerank | Δ (rerank - baseline) |",
        "|---|---:|---:|---:|",
    ]
    for key in METRIC_KEYS:
        b = baseline["metrics"].get(key)
        r = rerank["metrics"].get(key)
        delta = r - b if isinstance(r, (int, float)) and isinstance(b, (int, float)) else None
        lines.append(f"| `{key}` | {fmt(b)} | {fmt(r)} | {fmt(delta)} |")

    lines += ["", "### Expected source 的 rank 变化", "", "| Expected source | Baseline rank | Rerank rank | Change |", "|---|---:|---:|---:|"]
    for source in expected:
        b = base_ranks.get(source)
        r = rerank_ranks.get(source)
        change = r - b if b is not None and r is not None else None
        change_text = "—" if change is None else (f"{change:+d}" if change else "0")
        lines.append(f"| `{cell(source)}` | {fmt(b)} | {fmt(r)} | {change_text} |")

    base_top5 = {item["source"] for item in base_items[:5]}
    rerank_top5 = {item["source"] for item in rerank_items[:5]}
    lines += [
        "",
        "### Top 5 变动",
        "",
        f"- 移出 Top 5（baseline → rerank）：{', '.join(f'`{cell(s)}`' for s in sorted(base_top5 - rerank_top5)) or '无'}",
        f"- 移入 Top 5（rerank 相对 baseline）：{', '.join(f'`{cell(s)}`' for s in sorted(rerank_top5 - base_top5)) or '无'}",
        "",
    ]
    lines += render_top10("Baseline", baseline) + [""] + render_top10("Rerank", rerank) + [""]
    return lines


def build_markdown(report: dict[str, Any]) -> str:
    strategies = report["strategies"]
    cases = {
        strategy: {case["case_id"]: case for case in data["cases"]}
        for strategy, data in strategies.items()
    }
    missing = [case_id for case_id in CASE_IDS if any(case_id not in cases[s] for s in ("baseline", "rerank"))]
    if missing:
        raise ValueError(f"Missing cases in benchmark report: {', '.join(missing)}")

    lines = [
        "# Reranking benchmark selected-case analysis",
        "",
        f"- Source report: `{report.get('timestamp_utc', '—')}`",
        f"- Report schema: `{report.get('schema_version', '—')}`",
        f"- final K: `{report.get('final_k', '—')}`",
        f"- Scope: {len(CASE_IDS)} selected cases; only final Top 10 is included.",
        "",
        "> 本文由提取脚本根据现有 benchmark JSON 生成；未重新运行 retrieval 或 reranker。",
        "",
    ]
    for case_id in CASE_IDS:
        lines.extend(render_case(case_id, cases["baseline"][case_id], cases["rerank"][case_id]))
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Existing reranking benchmark JSON")
    parser.add_argument("--output", type=Path, required=True, help="Markdown output path")
    args = parser.parse_args()

    report = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_markdown(report), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
