"""Normalize and format the inputs shared by every generation section."""

from __future__ import annotations

from typing import Any

from app.tools.generation.schemas import GenerationContext


def format_retrieved_context(retrieved_chunks: list[dict[str, Any]]) -> str:
    """Expose chunks as stable knowledge-item numbers, without raw source IDs."""
    if not retrieved_chunks:
        return "未检索到相关管理知识。"

    items = []
    for index, item in enumerate(retrieved_chunks, start=1):
        items.append(
            f"知识项{index}（Knowledge item {index}）\n"
            f"章节：{item.get('chapter_title', '')}\n"
            f"小节：{item.get('section_title', '')}\n"
            f"标题：{item.get('title', '')}\n"
            f"正文：\n{item.get('content', '')}"
        )
    return "\n\n".join(items)


def build_generation_context(
    *,
    description: str,
    problem_types: list[str] | None,
    retrieved_chunks: list[dict[str, Any]] | None,
) -> GenerationContext:
    chunks = list(retrieved_chunks or [])
    return {
        "description": description,
        "problem_types": list(problem_types or []),
        "retrieved_chunks": chunks,
        "retrieved_context": format_retrieved_context(chunks),
        "core_diagnosis": None,
        "root_causes": None,
    }
