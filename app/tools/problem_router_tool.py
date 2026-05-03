from __future__ import annotations


PROBLEM_KEYWORDS: dict[str, list[str]] = {
    "customer_value_misalignment": [
        "顾客",
        "客户",
        "用户",
        "新客户",
        "客户减少",
        "增长放缓",
        "增长变慢",
        "价值",
        "客户价值",
        "顾客价值",
        "需求",
        "产品没人用",
        "转化下降",
        "复购下降",
    ],
    "opportunity_neglect": [
        "机会",
        "创新",
        "新市场",
        "新产品",
        "探索",
        "开拓",
        "增长机会",
        "未来",
        "试错",
        "业务停滞",
        "没有新方向",
    ],
    "strategy_execution_gap": [
        "战略",
        "执行",
        "落地",
        "协同",
        "部门",
        "资源",
        "战略目标",
        "战略不清楚",
        "各做各的",
        "目标传递",
        "组织承接",
    ],
    "metrics_misalignment": [
        "指标",
        "KPI",
        "考核",
        "衡量",
        "数据",
        "目标",
        "目标混乱",
        "成本",
        "效率",
        "降本增效",
        "绩效",
        "短期指标",
    ],
    "control_over_self_drive": [
        "管控",
        "审批",
        "流程",
        "员工",
        "责任",
        "授权",
        "自驱",
        "主动性",
        "被动",
        "很忙",
        "只是在完成任务",
        "等指令",
        "目标不清楚",
    ],
    "short_term_decision_bias": [
        "短期",
        "今天",
        "长期",
        "未来",
        "决策",
        "短期收益",
        "只看眼前",
        "长期能力",
        "牺牲长期",
    ],
    "entrepreneurial_leadership_gap": [
        "企业家",
        "领导力",
        "老板",
        "管理层",
        "负责人",
        "使命",
        "责任",
        "决策能力",
        "方向感",
        "领导团队",
    ],
}


def route_problem(company_context: str, goal: str | None = None) -> list[str]:
    text = f"{company_context}\n{goal or ''}".lower()

    matched_types: list[str] = []

    for problem_type, keywords in PROBLEM_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            matched_types.append(problem_type)

    if not matched_types:
        matched_types.append("general_management_diagnosis")

    return matched_types