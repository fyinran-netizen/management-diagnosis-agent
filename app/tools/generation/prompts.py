from __future__ import annotations

from typing import Any


def format_retrieved_context(retrieved_chunks: list[dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return "未检索到相关管理知识。"

    return "\n\n".join(
        [
            (
                f"知识项{index}\n"
                f"章节：{item.get('chapter_title', '')}\n"
                f"小节：{item.get('section_title', '')}\n"
                f"标题：{item.get('title', '')}\n"
                f"正文：\n{item.get('content', '')}"
            )
            for index, item in enumerate(retrieved_chunks, start=1)
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
    diagnosis_summary: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    # 保留这些字段仅用于接口兼容，当前 generation baseline 不使用。
    del language, problem_types, diagnosis_hints, diagnosis_summary

    retrieved_context = format_retrieved_context(retrieved_chunks)

    return [
        {
            "role": "system",
            "content": (
                "你是一名面向企业管理者的管理诊断助手。"
                "请基于用户提供的企业问题和检索到的管理知识进行分析，并始终使用中文输出。"
                "不得编造用户未提供的企业事实；信息不足时，应明确说明缺失信息或必要假设。"
                "分析应主要依据检索到的知识，避免空泛建议。"
                "输出采用以下五个部分："
                "1. 核心诊断；"
                "2. 相关管理概念；"
                "3. 可能的根本原因；"
                "4. 实际建议；"
                "5. 缺失信息与假设。"
                "每个部分如使用了检索知识，应在该部分末尾标注相关知识项，"
                "例如“依据：知识项1、知识项3”。"
                "不要求逐句引用，但引用的知识项必须能够支持对应分析。"
                "不得输出原始文件名、文件路径或内部来源ID。"
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"企业问题：\n{company_context}\n\n"
                f"分析目标：\n{goal or '未指定'}\n\n"
                f"检索到的管理知识：\n{retrieved_context}"
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
                "Do not include source file paths, source IDs, or raw filename citations in the final report. "
                "When grounding claims in retrieved content, cite the item as 知识项1, 知识项2, etc. "
                "For English output, use Knowledge item 1, Knowledge item 2, etc. Only cite provided items. "
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
                "Keep the required knowledge item citations (知识项1 for Chinese or Knowledge item 1 for English) when making grounded claims. "
                "Do not include any word count or length note."
            ),
        },
    ]
