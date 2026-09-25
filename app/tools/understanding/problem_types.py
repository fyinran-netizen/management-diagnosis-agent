from __future__ import annotations


# Stable values are used in AgentState and passed through the workflow.  The
# labels are presentation/query text only.
PROBLEM_TYPE_LABELS: dict[str, str] = {
    "customer_value_misalignment": "客户价值错配",
    "opportunity_neglect": "机会忽视",
    "strategy_execution_gap": "战略执行脱节",
    "metrics_misalignment": "指标错配",
    "control_over_self_drive": "对自驱力的过度控制",
    "short_term_decision_bias": "短期决策偏差",
    "entrepreneurial_leadership_gap": "企业家领导力缺口",
    "general_management_diagnosis": "一般管理诊断",
    "other": "其他",
}

PROBLEM_TYPE_CODES = tuple(PROBLEM_TYPE_LABELS)


def problem_type_label(code: str) -> str:
    return PROBLEM_TYPE_LABELS.get(code, code)
