from __future__ import annotations

import os
import re
from dataclasses import asdict
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

from app.rag.ingest import load_knowledge_base


load_dotenv()

def should_use_private_knowledge() -> bool:
    value = os.getenv("USE_PRIVATE_KNOWLEDGE", "false").lower().strip()
    return value in {"true", "1", "yes", "y"}


KEYWORD_MAP: dict[str, list[str]] = {
    "customer_value": [
        "顾客",
        "客户",
        "用户",
        "新客户",
        "价值",
        "创造顾客",
        "客户减少",
        "增长放缓",
    ],
    "opportunity": [
        "机会",
        "增长",
        "创新",
        "未来",
        "新市场",
        "新产品",
        "探索",
        "开拓",
    ],
    "strategy_organization": [
        "战略",
        "组织",
        "部门",
        "协同",
        "执行",
        "资源",
        "目标传递",
    ],
    "metrics": [
        "指标",
        "KPI",
        "考核",
        "衡量",
        "数据",
        "目标",
        "效率",
        "成本",
    ],
    "self_drive": [
        "自驱",
        "管控",
        "审批",
        "员工",
        "责任",
        "授权",
        "目标混乱",
        "忙",
    ],
}


@lru_cache(maxsize=1)
def get_cached_chunks() -> tuple:
    return tuple(
        load_knowledge_base(
            include_private=should_use_private_knowledge()
        )
    )


def normalize_text(text: str) -> str:
    return text.lower().strip()


def extract_query_terms(query: str) -> list[str]:
    normalized_query = normalize_text(query)

    terms: list[str] = []

    for keywords in KEYWORD_MAP.values():
        for keyword in keywords:
            if keyword.lower() in normalized_query:
                terms.append(keyword.lower())

    english_terms = re.findall(r"[a-zA-Z]{3,}", normalized_query)
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,}", normalized_query)

    terms.extend(english_terms)
    terms.extend(chinese_terms)

    return list(dict.fromkeys(terms))


def score_chunk(query: str, chunk_text: str) -> int:
    terms = extract_query_terms(query)
    normalized_query = normalize_text(query)
    normalized_chunk = normalize_text(chunk_text)

    score = 0

    for term in terms:
        if term in normalized_chunk:
            score += 2

    for keywords in KEYWORD_MAP.values():
        query_hits = sum(
            1 for keyword in keywords if keyword.lower() in normalized_query
        )
        chunk_hits = sum(
            1 for keyword in keywords if keyword.lower() in normalized_chunk
        )

        if query_hits and chunk_hits:
            score += query_hits + chunk_hits

    return score


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    chunks = get_cached_chunks()
    scored_chunks: list[dict[str, Any]] = []

    for chunk in chunks:
        combined_text = f"{chunk.title}\n{chunk.content}"
        score = score_chunk(query, combined_text)

        if score > 0:
            chunk_dict = asdict(chunk)
            chunk_dict["score"] = score
            scored_chunks.append(chunk_dict)

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)

    return scored_chunks[:top_k]