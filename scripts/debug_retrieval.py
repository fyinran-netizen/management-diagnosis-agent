from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

from app.tools.retrieval.retrievers.embedding import retrieve_by_embedding
from app.tools.retrieval.retrievers.hybrid_linear import hybrid_retrieve
from app.tools.retrieval.retrievers.keyword import retrieve_by_keyword


def print_results(title: str, results: list[dict[str, Any]], preview_chars: int) -> None:
    print(f"\n## {title}")
    if not results:
        print("No results.")
        return

    for index, item in enumerate(results, start=1):
        preview = " ".join(item.get("content", "").split())[:preview_chars]
        print(f"\n[{index}] {item.get('source')} | {item.get('title')}")
        print(f"method: {item.get('retrieval_method')}")
        print(f"score: {item.get('score')}")
        print(f"keyword_score: {item.get('keyword_score', 0)}")
        print(f"embedding_score: {item.get('embedding_score', 0)}")
        print(f"hybrid_score: {item.get('hybrid_score', 0)}")
        print(f"preview: {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect keyword, embedding, and hybrid retrieval results.")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--preview-chars", type=int, default=220)
    args = parser.parse_args()

    print(f"query: {args.query}")
    print_results("Keyword", retrieve_by_keyword(args.query, top_k=args.top_k), args.preview_chars)
    print_results("Embedding", retrieve_by_embedding(args.query, top_k=args.top_k), args.preview_chars)
    print_results("Hybrid", hybrid_retrieve(args.query, top_k=args.top_k), args.preview_chars)


if __name__ == "__main__":
    main()
