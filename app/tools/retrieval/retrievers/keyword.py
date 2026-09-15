from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path

from app.core.config import PRIVATE_KNOWLEDGE_DIR
from app.tools.retrieval.retrievers.bm25 import (
    EXCLUDED_SOURCES, KEYWORD_MAP, extract_query_terms, get_cached_chunks,
    normalize_text, tokenize_for_bm25,
)
from app.tools.retrieval.schemas import RetrievedChunk


def retrieve_by_keyword(
    query: str,
    top_k: int = 5,
    *,
    corpus_dir: Path = PRIVATE_KNOWLEDGE_DIR,
) -> list[RetrievedChunk]:
    """Naive keyword baseline: term occurrence counts, without BM25 weighting."""
    query_terms = extract_query_terms(query)
    normalized_query = normalize_text(query)
    scored: list[RetrievedChunk] = []
    for chunk in get_cached_chunks(corpus_dir):
        text = normalize_text("\n".join(str(value) for value in (chunk.chapter_title, chunk.section_title, chunk.title, chunk.content)))
        tokens = Counter(tokenize_for_bm25(text))
        score = float(sum(tokens[term] for term in query_terms))
        score += float(sum(1 for keywords in KEYWORD_MAP.values() for keyword in keywords if keyword.lower() in normalized_query and keyword.lower() in text))
        if score <= 0 or chunk.source in EXCLUDED_SOURCES:
            continue
        item: RetrievedChunk = asdict(chunk)
        item.update(score=score, keyword_score=score, retrieval_method="keyword")
        scored.append(item)
    scored.sort(key=lambda item: float(item["score"]), reverse=True)
    for rank, item in enumerate(scored, 1):
        item["rank"] = rank
        item["keyword_rank"] = rank
    return scored[:top_k]
