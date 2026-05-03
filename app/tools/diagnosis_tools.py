from __future__ import annotations


DIAGNOSIS_HINTS: dict[str, str] = {
    "customer_value_misalignment": (
        "Focus on whether the company has lost clarity about its core customers, "
        "whether internal efficiency is being mistaken for customer value creation, "
        "and whether current work truly improves customer value."
    ),
    "opportunity_neglect": (
        "Focus on whether management is only solving current problems instead of identifying "
        "future opportunities, new customer needs, new products, or new markets."
    ),
    "strategy_execution_gap": (
        "Focus on whether strategy is actually carried by organizational structure, resources, "
        "department goals, roles, processes, and daily decisions."
    ),
    "metrics_misalignment": (
        "Focus on whether KPIs and metrics serve the real business goal, or whether they distort "
        "employee behavior and weaken customer value."
    ),
    "control_over_self_drive": (
        "Focus on whether excessive control, approval, or task-based management is weakening "
        "employee responsibility, initiative, and self-driven action."
    ),
    "short_term_decision_bias": (
        "Focus on whether current decisions are over-optimized for short-term efficiency or cost "
        "while weakening future value creation and long-term capability."
    ),
    "entrepreneurial_leadership_gap": (
        "Focus on whether leadership has enough clarity about mission, opportunity, responsibility, "
        "and decision-making discipline."
    ),
    "general_management_diagnosis": (
        "Provide a general management diagnosis based on customer value, opportunity, strategy, "
        "metrics, organizational responsibility, and future-oriented decision making."
    ),
}


def build_diagnosis_hints(problem_types: list[str]) -> list[str]:
    if not problem_types:
        return [DIAGNOSIS_HINTS["general_management_diagnosis"]]

    return [
        DIAGNOSIS_HINTS.get(problem_type, DIAGNOSIS_HINTS["general_management_diagnosis"])
        for problem_type in problem_types
    ]