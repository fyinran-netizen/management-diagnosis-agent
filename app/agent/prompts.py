from __future__ import annotations

from typing import Any


def format_retrieved_context(retrieved_chunks: list[dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return "No relevant knowledge base content was retrieved."

    return "\n\n".join(
        [
            f"[Source: {item['source']} | Section: {item['title']}]\n{item['content']}"
            for item in retrieved_chunks
        ]
    )


def format_diagnosis_hints(diagnosis_hints: list[str] | None) -> str:
    if not diagnosis_hints:
        return "No specific diagnosis hints were generated."

    return "\n".join([f"- {hint}" for hint in diagnosis_hints])


def build_generation_messages(
    company_context: str,
    goal: str | None,
    language: str,
    retrieved_chunks: list[dict[str, Any]],
    problem_types: list[str] | None = None,
    diagnosis_hints: list[str] | None = None,
) -> list[dict[str, str]]:
    output_language = "Chinese" if language == "zh" else "English"
    retrieved_context = format_retrieved_context(retrieved_chunks)

    problem_types_text = ", ".join(problem_types or ["general_management_diagnosis"])
    diagnosis_hints_text = format_diagnosis_hints(diagnosis_hints)

    return [
        {
            "role": "system",
            "content": (
                "You are a management diagnosis assistant for enterprise managers. "
                "Use the retrieved management knowledge as the main basis for your diagnosis. "
                "Do not invent company facts. If information is missing, clearly state the assumptions. "
                "Do not use hidden reasoning. Give the final answer directly. "
                "Use a calm, professional consulting style. "
                "Do not include word count, character count, token count, or any length note."
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Output language: {output_language}\n\n"
                f"Company context:\n{company_context}\n\n"
                f"Analysis goal:\n{goal}\n\n"
                f"Detected problem types:\n{problem_types_text}\n\n"
                f"Diagnosis hints:\n{diagnosis_hints_text}\n\n"
                f"Retrieved management knowledge:\n{retrieved_context}\n\n"
                "Please provide a concise structured management diagnosis. "
                "Keep the report around 600-800 Chinese characters if output is Chinese.\n\n"
                "Use the following sections:\n"
                "1. Core diagnosis\n"
                "2. Related management concepts from the knowledge base\n"
                "3. Possible root causes\n"
                "4. Practical recommendations\n"
                "5. Missing information and assumptions\n\n"
                "Important requirements:\n"
                "- Ground your diagnosis in the retrieved management knowledge.\n"
                "- Use the detected problem types and diagnosis hints to guide the analysis.\n"
                "- Avoid generic advice.\n"
                "- Clearly separate known facts from assumptions.\n"
                "- Mention the source files when using retrieved concepts.\n"
                "- Do not include any word count or length note."
            ),
        },
    ]


def build_revision_messages(
    company_context: str,
    goal: str | None,
    language: str,
    retrieved_chunks: list[dict[str, Any]],
    current_report: str,
    issues: list[str],
) -> list[dict[str, str]]:
    output_language = "Chinese" if language == "zh" else "English"
    retrieved_context = format_retrieved_context(retrieved_chunks)

    return [
        {
            "role": "system",
            "content": (
                "You revise management diagnosis reports. "
                "Fix the listed issues only. "
                "Do not invent new company facts. "
                "Use the retrieved knowledge as the basis. "
                "Do not use hidden reasoning. "
                "Give the final revised report directly. "
                "Do not include word count, character count, token count, or any length note."
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Output language: {output_language}\n\n"
                f"Company context:\n{company_context}\n\n"
                f"Analysis goal:\n{goal}\n\n"
                f"Retrieved management knowledge:\n{retrieved_context}\n\n"
                f"Current report:\n{current_report}\n\n"
                f"Issues to fix:\n{issues}\n\n"
                "Rewrite the report in around 500-700 Chinese characters if output is Chinese.\n"
                "Use exactly these sections:\n"
                "1. Core diagnosis\n"
                "2. Knowledge base basis\n"
                "3. Root causes\n"
                "4. Practical recommendations\n"
                "5. Missing information and assumptions\n\n"
                "The revised report must include practical recommendations and missing information/assumptions. "
                "Do not include any word count or length note."
            ),
        },
    ]