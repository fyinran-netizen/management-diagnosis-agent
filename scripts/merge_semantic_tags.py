from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "private_knowledge_base" / "semantic_metadata.jsonl"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "private_knowledge_base" / "semantic_metadata_merged.jsonl"

ENGLISH_DIAGNOSIS_TAGS = [
    "customer_value_misalignment",
    "opportunity_neglect",
    "strategy_execution_gap",
    "metrics_misalignment",
    "control_over_self_drive",
    "short_term_decision_bias",
    "entrepreneurial_leadership_gap",
    "general_management_diagnosis",
]

ZH_LABEL_TO_TAG = {
    "\u5ba2\u6237\u4ef7\u503c\u9519\u4f4d": "customer_value_misalignment",
    "\u673a\u4f1a\u8bc6\u522b\u4e0d\u8db3": "opportunity_neglect",
    "\u6218\u7565\u6267\u884c\u8131\u8282": "strategy_execution_gap",
    "\u6307\u6807\u4f53\u7cfb\u9519\u4f4d": "metrics_misalignment",
    "\u8fc7\u5ea6\u63a7\u5236\u6291\u5236\u81ea\u9a71": "control_over_self_drive",
    "\u77ed\u671f\u51b3\u7b56\u504f\u5dee": "short_term_decision_bias",
    "\u4f01\u4e1a\u5bb6\u9886\u5bfc\u529b\u7f3a\u53e3": "entrepreneurial_leadership_gap",
    "\u901a\u7528\u7ba1\u7406\u95ee\u9898": "general_management_diagnosis",
}


@dataclass(frozen=True)
class MergeResult:
    record: dict[str, Any]
    mapped_labels: list[str]
    unmapped_labels: list[str]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"Line {line_number} is not a JSON object: {path}")
        records.append(item)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def ensure_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def merge_diagnosis_tags(
    record: dict[str, Any],
    label_to_tag: dict[str, str] | None = None,
) -> MergeResult:
    label_to_tag = label_to_tag or ZH_LABEL_TO_TAG
    merged = copy.deepcopy(record)
    inferred = merged.setdefault("inferred", {})
    if not isinstance(inferred, dict):
        inferred = {}
        merged["inferred"] = inferred

    labels = ensure_string_list(inferred.get("diagnosis_labels_zh"))
    existing_tags = [
        tag
        for tag in ensure_string_list(inferred.get("diagnosis_tags"))
        if tag in ENGLISH_DIAGNOSIS_TAGS
    ]

    tags = list(existing_tags)
    mapped_labels: list[str] = []
    unmapped_labels: list[str] = []
    for label in labels:
        tag = label_to_tag.get(label)
        if tag is None:
            unmapped_labels.append(label)
            continue
        mapped_labels.append(label)
        if tag not in tags:
            tags.append(tag)

    inferred["diagnosis_tags"] = tags
    return MergeResult(record=merged, mapped_labels=mapped_labels, unmapped_labels=unmapped_labels)


def merge_records(
    records: list[dict[str, Any]],
    *,
    pending_only: bool = False,
) -> tuple[list[dict[str, Any]], list[MergeResult]]:
    merged_records: list[dict[str, Any]] = []
    results: list[MergeResult] = []

    for record in records:
        if pending_only and record.get("review", {}).get("status") != "pending":
            merged_records.append(copy.deepcopy(record))
            continue
        result = merge_diagnosis_tags(record)
        merged_records.append(result.record)
        results.append(result)

    return merged_records, results


def print_summary(records: list[dict[str, Any]], results: list[MergeResult]) -> None:
    tag_counts = Counter(
        tag
        for record in records
        for tag in record.get("inferred", {}).get("diagnosis_tags", [])
    )
    unmapped_counts = Counter(label for result in results for label in result.unmapped_labels)
    mapped_record_count = sum(bool(result.mapped_labels) for result in results)
    tagged_record_count = sum(
        bool(record.get("inferred", {}).get("diagnosis_tags"))
        for record in records
    )

    print(f"records: {len(records)}")
    print(f"records_with_mapped_labels: {mapped_record_count}")
    print(f"records_with_tags: {tagged_record_count}")
    print("tag_counts:")
    for tag, count in tag_counts.most_common():
        print(f"  {tag}: {count}")
    print("unmapped_label_counts:")
    for label, count in unmapped_counts.most_common():
        print(f"  {label}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge qwen Chinese candidate diagnosis labels into standard diagnosis_tags.",
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--pending-only",
        action="store_true",
        help="Only merge records whose review.status is pending.",
    )
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    records = read_jsonl(args.input)
    merged_records, results = merge_records(records, pending_only=args.pending_only)
    print_summary(merged_records, results)

    if not args.no_write:
        write_jsonl(args.output, merged_records)
        print(f"wrote: {args.output}")


if __name__ == "__main__":
    main()
