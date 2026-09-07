from __future__ import annotations

from typing import Any

from app.core.config import GENERATION_MODEL
from app.llm.ollama_client import chat_with_ollama
from app.tools.generation.prompts import build_generation_messages, build_revision_messages


def generate_report(*, company_context: str, goal: str | None, language: str,
                    retrieved_chunks: list[dict[str, Any]], problem_types: list[str],
                    diagnosis_hints: list[str], diagnosis_summary: dict[str, Any]) -> str:
    messages = build_generation_messages(company_context, goal, language, retrieved_chunks, problem_types, diagnosis_hints, diagnosis_summary)
    return chat_with_ollama(messages, model=GENERATION_MODEL)


def revise_report(*, company_context: str, goal: str | None, language: str,
                  retrieved_chunks: list[dict[str, Any]], current_report: str,
                  issues: list[str]) -> str:
    messages = build_revision_messages(company_context, goal, language, retrieved_chunks, current_report, issues)
    return chat_with_ollama(messages, model=GENERATION_MODEL)
