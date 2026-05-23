from __future__ import annotations

import re
from typing import Any


MIN_DESCRIPTION_CHARS = 20
MIN_SIGNAL_TERMS = 2

MANAGEMENT_SIGNAL_TERMS = [
    "客户",
    "顾客",
    "用户",
    "增长",
    "战略",
    "组织",
    "团队",
    "指标",
    "KPI",
    "考核",
    "效率",
    "成本",
    "员工",
    "管理",
    "决策",
    "机会",
    "价值",
    "复购",
    "销售",
    "营销",
    "目标",
    "流程",
    "授权",
    "责任",
]

VAGUE_PATTERNS = [
    "帮我看看",
    "给点建议",
    "怎么管理",
    "有问题",
    "不太好",
    "怎么办",
]


def check_problem_clarity(description: str) -> dict[str, Any]:
    text = description.strip()
    issues: list[str] = []

    if len(text) < MIN_DESCRIPTION_CHARS:
        issues.append("The problem description is too short.")

    signal_hits = [
        term for term in MANAGEMENT_SIGNAL_TERMS
        if term.lower() in text.lower()
    ]
    if len(signal_hits) < MIN_SIGNAL_TERMS:
        issues.append("The description has too few management diagnosis signals.")

    if any(pattern in text for pattern in VAGUE_PATTERNS) and len(text) < 40:
        issues.append("The request is too vague to diagnose responsibly.")

    is_clear = not issues
    questions = [] if is_clear else [
        "请补充当前最明显的业务或管理症状是什么，例如增长、客户、组织、指标或团队行为的变化。",
        "请说明这个问题已经持续多久，以及你最希望诊断的决策目标是什么。",
        "请提供一两个具体事实或数据，例如新客户、复购、成本、效率、员工行为或部门协同情况。",
    ]

    return {
        "is_clear": is_clear,
        "issues": issues,
        "signal_terms": signal_hits,
        "questions": questions,
    }
