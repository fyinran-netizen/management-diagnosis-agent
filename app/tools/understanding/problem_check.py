from __future__ import annotations

from typing import Any


MIN_DESCRIPTION_CHARS = 20
MIN_SIGNAL_TERMS = 2

MANAGEMENT_SIGNAL_TERMS = [
    "客户", "用户", "增长", "战略", "组织", "团队",
    "指标", "KPI", "效率", "成本", "员工", "管理",
    "决策", "价值", "销售", "目标", "流程", "授权", "责任",
]

CONCRETE_PROBLEM_TERMS = [
    "下降", "下滑", "减少", "增加", "上升",
    "流失", "投诉", "离职", "延期", "返工",
    "亏损", "利润", "复购", "续约",
    "审批", "冲突", "积压", "主动性",
]

VAGUE_PATTERNS = [
    "帮我看看",
    "给点建议",
    "有问题",
    "不太好",
    "状态不好",
    "业绩一般",
    "怎么办",
]


def check_problem_clarity(description: str) -> dict[str, Any]:
    text = description.strip()
    lower_text = text.lower()

    issues: list[str] = []

    signal_hits = [
        term for term in MANAGEMENT_SIGNAL_TERMS
        if term.lower() in lower_text
    ]

    concrete_hits = [
        term for term in CONCRETE_PROBLEM_TERMS
        if term.lower() in lower_text
    ]

    vague_hits = [
        term for term in VAGUE_PATTERNS
        if term.lower() in lower_text
    ]

    if len(text) < MIN_DESCRIPTION_CHARS:
        issues.append("The problem description is too short.")

    if len(signal_hits) < MIN_SIGNAL_TERMS:
        issues.append("The description has too few management diagnosis signals.")

    if not concrete_hits:
        issues.append("The description lacks a concrete management symptom or fact.")

    if vague_hits and not concrete_hits:
        issues.append("The request is too vague to diagnose responsibly.")

    is_clear = not issues

    questions = [] if is_clear else [
        "请说明当前最明显的业务或管理问题是什么。",
        "请提供一两个具体变化或事实，例如客户流失、业绩下降、员工离职、流程效率或 KPI 行为变化。",
        "你最希望解决或诊断的问题是什么？",
    ]

    return {
        "is_clear": is_clear,
        "issues": issues,
        "signal_terms": signal_hits,
        "concrete_terms": concrete_hits,
        "questions": questions,
    }