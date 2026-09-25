from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Any
from pathlib import Path

from app.tools.ingestion.repositories import FilesystemArtifactRepository
from app.core.config import (
    PRIVATE_KNOWLEDGE_DIR,
    PRODUCTION_RETRIEVAL_CORPUS_DIR,
)
from app.tools.retrieval.schemas import RetrievedChunk


EXCLUDED_SOURCES = {"99_private_test.md"}
SEMANTIC_METADATA_PATH = PRODUCTION_RETRIEVAL_CORPUS_DIR / "semantic_metadata.jsonl"
BM25_METADATA_MODES = {"base", "unweighted", "weighted"}
PRODUCTION_BM25_METADATA_MODE = "unweighted"

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


@lru_cache(maxsize=8)
def get_cached_chunks(corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> tuple:
    chunks = FilesystemArtifactRepository(corpus_dir).load_chunks()
    return tuple({
        "source": chunk.source,
        "title": chunk.title,
        "content": chunk.content,
        "chapter_title": chunk.chapter_title,
        "section_title": chunk.section_title,
        "chunk_index": chunk.chunk_index,
        "chunk_count": chunk.chunk_count,
    } for chunk in chunks if chunk.source not in EXCLUDED_SOURCES)


def normalize_text(text: str) -> str:
    return text.lower().strip()


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


def semantic_metadata_to_search_text(
    record: dict[str, Any], *, weighted: bool = True
) -> str:
    """Build metadata text; production BM25 uses the unweighted loader below.

    The weighted option remains only for historical ablation compatibility. It
    is not used by ``retrieve_by_keyword``'s production default path.
    """
    parts: list[str] = []
    for field_path, weight in SEMANTIC_METADATA_FIELD_WEIGHTS.items():
        text = values_to_text(nested_value(record, field_path))
        if text:
            parts.extend([text] * (weight if weighted else 1))
    return "\n".join(parts)


@lru_cache(maxsize=8)
def load_source_id_to_path(corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> dict[str, str]:
    records = FilesystemArtifactRepository(corpus_dir).load_source_metadata()
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


@lru_cache(maxsize=8)
def load_semantic_metadata_records(
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
) -> tuple[dict[str, Any], ...]:
    return tuple(FilesystemArtifactRepository(corpus_dir).load_semantic_metadata())


@lru_cache(maxsize=8)
def load_semantic_metadata_by_source(corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> dict[str, str]:
    source_id_to_path = load_source_id_to_path(corpus_dir)
    metadata_by_source: dict[str, str] = {}
    for record in load_semantic_metadata_records(corpus_dir):
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


@lru_cache(maxsize=8)
def load_semantic_summaries_by_source(corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> dict[str, str]:
    """Expose summaries already present in the semantic metadata artifacts."""
    source_id_to_path = load_source_id_to_path(corpus_dir)
    summaries: dict[str, str] = {}
    for record in load_semantic_metadata_records(corpus_dir):
        source_id = record.get("source_id")
        summary = record.get("summary")
        source_path = source_id_to_path.get(source_id) if isinstance(source_id, str) else None
        if isinstance(source_path, str) and isinstance(summary, str) and summary.strip():
            summaries[source_path] = summary.strip()
    return summaries


@lru_cache(maxsize=8)
def load_semantic_metadata_by_source_unweighted(corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR) -> dict[str, str]:
    source_id_to_path = load_source_id_to_path(corpus_dir)
    metadata_by_source: dict[str, str] = {}
    for record in load_semantic_metadata_records(corpus_dir):
        source_id = record.get("source_id")
        if not isinstance(source_id, str):
            continue
        source_path = source_id_to_path.get(source_id)
        if source_path is None:
            continue
        text = semantic_metadata_to_search_text(record, weighted=False)
        if text:
            metadata_by_source[source_path] = text
    return metadata_by_source


def build_bm25_document_text(chunk: Any, semantic_text: str = "") -> str:
    get = chunk.get if isinstance(chunk, dict) else lambda key: getattr(chunk, key, None)
    parts = [
        get("chapter_title"),
        get("section_title"),
        get("title"),
        get("title"),
        get("content"),
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


@lru_cache(maxsize=3)
def get_cached_bm25_index(
    metadata_mode: str = PRODUCTION_BM25_METADATA_MODE,
    *,
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
) -> dict[str, Any]:
    if metadata_mode not in BM25_METADATA_MODES:
        raise ValueError(
            f"Unsupported BM25 metadata mode: {metadata_mode!r}. "
            f"Expected one of {sorted(BM25_METADATA_MODES)}."
        )
    chunks = get_cached_chunks(corpus_dir)
    if metadata_mode == "base":
        semantic_metadata_by_source: dict[str, str] = {}
        semantic_summaries_by_source: dict[str, str] = {}
    elif metadata_mode == "unweighted":
        semantic_metadata_by_source = load_semantic_metadata_by_source_unweighted(corpus_dir)
        semantic_summaries_by_source = load_semantic_summaries_by_source(corpus_dir)
    else:
        semantic_metadata_by_source = load_semantic_metadata_by_source(corpus_dir)
        semantic_summaries_by_source = load_semantic_summaries_by_source(corpus_dir)
    documents = []
    document_frequency: Counter[str] = Counter()

    for chunk in chunks:
        combined_text = build_bm25_document_text(
            chunk,
            semantic_metadata_by_source.get(chunk.get("source", ""), ""),
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
        "semantic_summaries_by_source": semantic_summaries_by_source,
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


def clear_bm25_caches() -> None:
    """Clear all BM25 inputs and indexes before a fresh process/run build."""
    get_cached_bm25_index.cache_clear()
    load_semantic_metadata_by_source.cache_clear()
    load_semantic_metadata_by_source_unweighted.cache_clear()
    load_semantic_summaries_by_source.cache_clear()
    load_semantic_metadata_records.cache_clear()
    load_source_id_to_path.cache_clear()
    get_cached_chunks.cache_clear()


def retrieve_by_keyword(
    query: str,
    top_k: int = 5,
    metadata_mode: str = PRODUCTION_BM25_METADATA_MODE,
    *,
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
) -> list[RetrievedChunk]:
    index = get_cached_bm25_index(metadata_mode, corpus_dir=corpus_dir)
    query_terms = tokenize_for_bm25(query)
    scored_chunks: list[RetrievedChunk] = []

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
            chunk_dict = dict(chunk)
            chunk_dict["score"] = score
            chunk_dict["keyword_score"] = score
            chunk_dict["bm25_score"] = score
            chunk_dict["retrieval_method"] = "keyword"
            summary = index["semantic_summaries_by_source"].get(chunk.get("source", ""))
            if summary:
                chunk_dict["summary"] = summary
            scored_chunks.append(chunk_dict)

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)
    for rank, item in enumerate(scored_chunks, start=1):
        item["rank"] = rank
        item["keyword_rank"] = rank

    return scored_chunks[:top_k]


def retrieve_by_bm25(
    query: str,
    top_k: int = 5,
    metadata_mode: str = PRODUCTION_BM25_METADATA_MODE,
    *,
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
) -> list[RetrievedChunk]:
    """Named BM25 entry point; metadata behavior is controlled by a parameter."""
    return retrieve_by_keyword(query, top_k=top_k, metadata_mode=metadata_mode, corpus_dir=corpus_dir)
