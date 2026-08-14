from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.rag.ingest import PRIVATE_KNOWLEDGE_DIR, iter_markdown_files, load_chunks_from_path


EXCLUDED_SOURCES = {"99_private_test.md"}
PRIVATE_INDEX_PATH = PRIVATE_KNOWLEDGE_DIR / "_index.json"
SEMANTIC_METADATA_CANDIDATES = (
    PRIVATE_KNOWLEDGE_DIR / "codex_metadata" / "semantic_metadata_merged.jsonl",
    PRIVATE_KNOWLEDGE_DIR / "semantic_metadata_merged.jsonl",
)

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

BM25_K1 = 1.5
BM25_B = 0.75

SEMANTIC_METADATA_FIELD_WEIGHTS = {
    ("summary",): 1,
    ("extracted", "concept_keywords"): 2,
    ("extracted", "method_keywords"): 2,
    ("extracted", "named_entities"): 2,
    ("inferred", "symptom_keywords"): 3,
    ("inferred", "diagnosis_labels_zh"): 3,
    ("inferred", "diagnosis_tags"): 3,
    ("inferred", "recommended_methods"): 2,
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            records.append(item)
    return records


def nested_value(item: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = item
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def values_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(
            text
            for item in value
            if isinstance(item, str) and (text := item.strip())
        )
    return ""


def semantic_metadata_to_search_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for field_path, weight in SEMANTIC_METADATA_FIELD_WEIGHTS.items():
        text = values_to_text(nested_value(record, field_path))
        if text:
            parts.extend([text] * weight)
    return "\n".join(parts)


@lru_cache(maxsize=1)
def load_source_id_to_path() -> dict[str, str]:
    if not PRIVATE_INDEX_PATH.exists():
        return {}

    records = json.loads(PRIVATE_INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        return {}

    mapping: dict[str, str] = {}
    for item in records:
        if not isinstance(item, dict):
            continue
        source_id = item.get("source_id")
        path = item.get("path")
        if isinstance(source_id, str) and isinstance(path, str):
            mapping[source_id] = path
    return mapping


@lru_cache(maxsize=1)
def load_semantic_metadata_by_source() -> dict[str, str]:
    metadata_path = next(
        (path for path in SEMANTIC_METADATA_CANDIDATES if path.exists()),
        None,
    )
    if metadata_path is None:
        return {}

    source_id_to_path = load_source_id_to_path()
    metadata_by_source: dict[str, str] = {}
    for record in read_jsonl(metadata_path):
        source_id = record.get("source_id")
        if not isinstance(source_id, str):
            continue
        source_path = source_id_to_path.get(source_id)
        if source_path is None:
            continue
        text = semantic_metadata_to_search_text(record)
        if text:
            metadata_by_source[source_path] = text
    return metadata_by_source


def build_bm25_document_text(chunk: Any, semantic_text: str = "") -> str:
    parts = [
        chunk.chapter_title,
        chunk.section_title,
        chunk.title,
        chunk.title,
        chunk.content,
        semantic_text,
    ]
    return "\n".join(str(part).strip() for part in parts if part)


def iter_keyword_terms(text: str) -> list[str]:
    normalized_text = normalize_text(text)
    terms: list[str] = []
    for keywords in KEYWORD_MAP.values():
        for keyword in keywords:
            keyword = keyword.lower()
            if keyword in normalized_text:
                terms.append(keyword)
    return terms


def tokenize_for_bm25(text: str) -> list[str]:
    normalized_text = normalize_text(text)
    terms = iter_keyword_terms(normalized_text)
    terms.extend(re.findall(r"[a-zA-Z]{3,}", normalized_text))

    for segment in re.findall(r"[\u4e00-\u9fff]{2,}", normalized_text):
        terms.append(segment)
        terms.extend(
            segment[index : index + 2]
            for index in range(0, max(len(segment) - 1, 0))
        )

    return terms


def extract_query_terms(query: str) -> list[str]:
    normalized_query = normalize_text(query)

    terms: list[str] = iter_keyword_terms(normalized_query)

    english_terms = re.findall(r"[a-zA-Z]{3,}", normalized_query)
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,}", normalized_query)

    terms.extend(english_terms)
    terms.extend(chinese_terms)

    return list(dict.fromkeys(terms))


def score_chunk(query: str, chunk_text: str) -> float:
    """Compatibility scorer for tests and ad-hoc debugging.

    `retrieve_by_keyword` uses a corpus-level BM25 index. This fallback keeps the
    old public helper useful when a caller only has one chunk of text.
    """
    terms = extract_query_terms(query)
    normalized_query = normalize_text(query)
    normalized_chunk = normalize_text(chunk_text)

    score = 0.0

    for term in terms:
        if term in normalized_chunk:
            score += 2.0

    for keywords in KEYWORD_MAP.values():
        query_hits = sum(
            1 for keyword in keywords if keyword.lower() in normalized_query
        )
        chunk_hits = sum(
            1 for keyword in keywords if keyword.lower() in normalized_chunk
        )

        if query_hits and chunk_hits:
            score += float(query_hits + chunk_hits)

    return score


@lru_cache(maxsize=1)
def get_cached_bm25_index() -> dict[str, Any]:
    chunks = get_cached_chunks()
    semantic_metadata_by_source = load_semantic_metadata_by_source()
    documents = []
    document_frequency: Counter[str] = Counter()

    for chunk in chunks:
        combined_text = build_bm25_document_text(
            chunk,
            semantic_metadata_by_source.get(chunk.source, ""),
        )
        term_frequencies = Counter(tokenize_for_bm25(combined_text))
        documents.append(
            {
                "chunk": chunk,
                "term_frequencies": term_frequencies,
                "length": sum(term_frequencies.values()),
            }
        )
        document_frequency.update(term_frequencies.keys())

    total_documents = len(documents)
    average_document_length = (
        sum(document["length"] for document in documents) / total_documents
        if total_documents
        else 0.0
    )
    return {
        "documents": tuple(documents),
        "document_frequency": document_frequency,
        "total_documents": total_documents,
        "average_document_length": average_document_length,
    }


def bm25_idf(total_documents: int, document_frequency: int) -> float:
    return math.log(
        1
        + (total_documents - document_frequency + 0.5)
        / (document_frequency + 0.5)
    )


def score_bm25_document(
    query_terms: list[str],
    term_frequencies: Counter[str],
    document_length: int,
    average_document_length: float,
    document_frequency: Counter[str],
    total_documents: int,
) -> float:
    if not query_terms or not document_length or not average_document_length:
        return 0.0

    score = 0.0
    unique_query_terms = Counter(query_terms)
    for term, query_frequency in unique_query_terms.items():
        term_frequency = term_frequencies.get(term, 0)
        if term_frequency <= 0:
            continue

        idf = bm25_idf(total_documents, document_frequency[term])
        denominator = term_frequency + BM25_K1 * (
            1 - BM25_B + BM25_B * document_length / average_document_length
        )
        score += (
            idf
            * (term_frequency * (BM25_K1 + 1) / denominator)
            * query_frequency
        )

    return score


def retrieve_by_keyword(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    index = get_cached_bm25_index()
    query_terms = tokenize_for_bm25(query)
    scored_chunks: list[dict[str, Any]] = []

    for document in index["documents"]:
        chunk = document["chunk"]
        score = score_bm25_document(
            query_terms=query_terms,
            term_frequencies=document["term_frequencies"],
            document_length=document["length"],
            average_document_length=index["average_document_length"],
            document_frequency=index["document_frequency"],
            total_documents=index["total_documents"],
        )

        if score > 0:
            chunk_dict = asdict(chunk)
            chunk_dict["score"] = score
            chunk_dict["keyword_score"] = score
            chunk_dict["retrieval_method"] = "keyword"
            scored_chunks.append(chunk_dict)

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)

    return scored_chunks[:top_k]
