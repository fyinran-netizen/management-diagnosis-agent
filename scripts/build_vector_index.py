from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.embeddings import embed_texts, get_embedding_cache_dir, get_embedding_model_name
from app.rag.ingest import PRIVATE_KNOWLEDGE_DIR, load_chunks_from_path, iter_markdown_files
from app.rag.vector_store import VECTOR_INDEX_DIR, chunk_to_embedding_text, save_vector_index


EXCLUDED_SOURCES = {"99_private_test.md"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local embedding index for RAG chunks.")
    parser.add_argument(
        "--include-sample",
        action="store_true",
        help="Also include sample knowledge chunks. The default index is private knowledge only.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--index-dir", type=Path, default=VECTOR_INDEX_DIR)
    args = parser.parse_args()

    chunks = []
    if args.include_sample:
        from app.rag.ingest import SAMPLE_KNOWLEDGE_DIR

        if SAMPLE_KNOWLEDGE_DIR.exists():
            for path in iter_markdown_files(SAMPLE_KNOWLEDGE_DIR):
                chunks.extend(load_chunks_from_path(path, SAMPLE_KNOWLEDGE_DIR))

    if PRIVATE_KNOWLEDGE_DIR.exists():
        for path in iter_markdown_files(
            PRIVATE_KNOWLEDGE_DIR,
            recursive=True,
            skipped_top_level_dirs={"ch00"},
        ):
            chunks.extend(load_chunks_from_path(path, PRIVATE_KNOWLEDGE_DIR))

    chunks = [chunk for chunk in chunks if chunk.source not in EXCLUDED_SOURCES]
    texts = [chunk_to_embedding_text(chunk) for chunk in chunks]
    embeddings = embed_texts(texts, batch_size=args.batch_size)

    metadata = {
        "model_name": get_embedding_model_name(),
        "cache_dir": str(get_embedding_cache_dir()),
        "include_sample": args.include_sample,
        "knowledge_scope": "sample+private" if args.include_sample else "private",
        "chunk_count": len(chunks),
        "embedding_dim": int(embeddings.shape[1]) if embeddings.size else 0,
        "created_at": datetime.now(UTC).isoformat(),
    }

    save_vector_index(chunks=chunks, embeddings=embeddings, metadata=metadata, index_dir=args.index_dir)

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"chunks_path: {args.index_dir / 'knowledge_chunks.json'}")
    print(f"embeddings_path: {args.index_dir / 'knowledge_embeddings.npy'}")
    print(f"metadata_path: {args.index_dir / 'index_metadata.json'}")


if __name__ == "__main__":
    main()
