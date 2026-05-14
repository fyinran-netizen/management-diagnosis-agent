from __future__ import annotations

import re
from dataclasses import asdict
from functools import lru_cache
from typing import Any

from app.rag.ingest import PRIVATE_KNOWLEDGE_DIR, iter_markdown_files, load_chunks_from_path


EXCLUDED_SOURCES = {"99_private_test.md"}

KEYWORD_MAP: dict[str, list[str]] = {
    "customer_value": [
        "\u987e\u5ba2",
        "\u5ba2\u6237",
        "\u7528\u6237",
        "\u65b0\u5ba2\u6237",
        "\u4ef7\u503c",
        "\u521b\u9020\u987e\u5ba2",
        "\u5ba2\u6237\u51cf\u5c11",
        "\u589e\u957f\u653e\u7f13",
    ],
    "opportunity": [
        "\u673a\u4f1a",
        "\u589e\u957f",
        "\u521b\u65b0",
        "\u672a\u6765",
        "\u65b0\u5e02\u573a",
        "\u65b0\u4ea7\u54c1",
        "\u63a2\u7d22",
        "\u5f00\u62d3",
    ],
    "strategy_organization": [
        "\u6218\u7565",
        "\u7ec4\u7ec7",
        "\u90e8\u95e8",
        "\u534f\u540c",
        "\u6267\u884c",
        "\u8d44\u6e90",
        "\u76ee\u6807\u4f20\u9012",
    ],
    "metrics": [
        "\u6307\u6807",
        "KPI",
        "\u8003\u6838",
        "\u8861\u91cf",
        "\u6570\u636e",
        "\u76ee\u6807",
        "\u6548\u7387",
        "\u6210\u672c",
    ],
    "self_drive": [
        "\u81ea\u9a71",
        "\u7ba1\u63a7",
        "\u5ba1\u6279",
        "\u5458\u5de5",
        "\u8d23\u4efb",
        "\u6388\u6743",
        "\u76ee\u6807\u6df7\u4e71",
        "\u5fd9",
    ],
}


@lru_cache(maxsize=1)
def get_cached_chunks() -> tuple:
    chunks = []
    if PRIVATE_KNOWLEDGE_DIR.exists():
        for path in iter_markdown_files(
            PRIVATE_KNOWLEDGE_DIR,
            recursive=True,
            skipped_top_level_dirs={"ch00"},
        ):
            chunks.extend(load_chunks_from_path(path, PRIVATE_KNOWLEDGE_DIR))

    return tuple(
        chunk
        for chunk in chunks
        if chunk.source not in EXCLUDED_SOURCES
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


def retrieve_by_keyword(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    chunks = get_cached_chunks()
    scored_chunks: list[dict[str, Any]] = []

    for chunk in chunks:
        combined_text = f"{chunk.title}\n{chunk.content}"
        score = score_chunk(query, combined_text)

        if score > 0:
            chunk_dict = asdict(chunk)
            chunk_dict["score"] = score
            chunk_dict["keyword_score"] = score
            chunk_dict["retrieval_method"] = "keyword"
            scored_chunks.append(chunk_dict)

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)

    return scored_chunks[:top_k]
