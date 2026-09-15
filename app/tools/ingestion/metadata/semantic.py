from __future__ import annotations

from collections.abc import Iterable
import copy
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from app.tools.ingestion.schemas import Chunk, Metadata

ENGLISH_DIAGNOSIS_TAGS = [
    "customer_value_misalignment", "opportunity_neglect", "strategy_execution_gap",
    "metrics_misalignment", "control_over_self_drive", "short_term_decision_bias",
    "entrepreneurial_leadership_gap", "general_management_diagnosis",
]
ZH_LABEL_TO_TAG = {
    "客户价值错位": "customer_value_misalignment", "机会识别不足": "opportunity_neglect",
    "战略执行脱节": "strategy_execution_gap", "指标体系错位": "metrics_misalignment",
    "过度控制抑制自驱": "control_over_self_drive", "短期决策偏差": "short_term_decision_bias",
    "企业家领导力缺口": "entrepreneurial_leadership_gap", "通用管理问题": "general_management_diagnosis",
}


@dataclass(frozen=True)
class MergeResult:
    record: dict[str, object]
    mapped_labels: list[str]
    unmapped_labels: list[str]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip() and item.strip() not in result:
            result.append(item.strip())
    return result


def merge_diagnosis_tags(record: dict[str, object], label_to_tag: dict[str, str] | None = None) -> MergeResult:
    merged = copy.deepcopy(record)
    inferred = merged.setdefault("inferred", {})
    if not isinstance(inferred, dict):
        inferred = {}
        merged["inferred"] = inferred
    labels = _string_list(inferred.get("diagnosis_labels_zh"))
    tags = [tag for tag in _string_list(inferred.get("diagnosis_tags")) if tag in ENGLISH_DIAGNOSIS_TAGS]
    mapped: list[str] = []
    unmapped: list[str] = []
    for label in labels:
        tag = (label_to_tag or ZH_LABEL_TO_TAG).get(label)
        if tag is None:
            unmapped.append(label)
        else:
            mapped.append(label)
            if tag not in tags:
                tags.append(tag)
    inferred["diagnosis_tags"] = tags
    return MergeResult(merged, mapped, unmapped)


def merge_records(records: list[dict[str, object]], *, pending_only: bool = False) -> tuple[list[dict[str, object]], list[MergeResult]]:
    merged: list[dict[str, object]] = []
    results: list[MergeResult] = []
    for record in records:
        if pending_only and record.get("review", {}).get("status") != "pending":
            merged.append(copy.deepcopy(record))
            continue
        result = merge_diagnosis_tags(record)
        merged.append(result.record)
        results.append(result)
    return merged, results


class SemanticMetadataProvider(Protocol):
    def get(self, chunks: Iterable[Chunk]) -> list[Metadata]: ...

