from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.retrieval.embeddings import embed_texts, get_embedding_cache_dir, get_embedding_model_name
from app.tools.ingestion import ingest
from app.tools.ingestion.repositories import FilesystemArtifactRepository
from app.core.config import SAMPLE_KNOWLEDGE_DIR, PRIVATE_KNOWLEDGE_DIR
from app.tools.retrieval.retrievers.bm25 import load_semantic_metadata_by_source_unweighted
from app.tools.retrieval.vector_store import (
    SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR,
    VECTOR_INDEX_DIR,
    chunk_to_embedding_text,
    save_vector_index,
)


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
    parser.add_argument("--corpus-dir", type=Path, default=PRIVATE_KNOWLEDGE_DIR)
    parser.add_argument(
        "--metadata-mode",
        choices=["base", "unweighted"],
        default="base",
        help="Document-side metadata configuration used to build embeddings.",
    )
    args = parser.parse_args()

    chunks = FilesystemArtifactRepository(args.corpus_dir).load_chunks()
    if args.include_sample:
        sample_paths = sorted(SAMPLE_KNOWLEDGE_DIR.glob("*.md"))
        chunks = [
            *chunks,
            *ingest(input_paths=sample_paths, persist=False).chunks,
        ]

    chunks = [chunk for chunk in chunks if chunk.source not in EXCLUDED_SOURCES]
    metadata_by_source = (
        load_semantic_metadata_by_source_unweighted(args.corpus_dir)
        if args.metadata_mode == "unweighted"
        else {}
    )
    texts = [
        "\n".join(
            part
            for part in [chunk_to_embedding_text(chunk), metadata_by_source.get(chunk.source, "")]
            if part
        )
        for chunk in chunks
    ]
    embeddings = embed_texts(texts, batch_size=args.batch_size)

    metadata = {
        "model_name": get_embedding_model_name(),
        "cache_dir": str(get_embedding_cache_dir()),
        "include_sample": args.include_sample,
        "knowledge_scope": "sample+private" if args.include_sample else "private",
        "metadata_mode": args.metadata_mode,
        "metadata_path": str(args.corpus_dir / "semantic_metadata.jsonl") if args.metadata_mode == "unweighted" else None,
        "embedding_text": "chunk structure + unweighted semantic metadata" if args.metadata_mode == "unweighted" else "chunk structure",
        "chunk_count": len(chunks),
        "embedding_dim": int(embeddings.shape[1]) if embeddings.size else 0,
        "created_at": datetime.now(UTC).isoformat(),
    }

    save_vector_index(chunks=chunks, embeddings=embeddings, metadata=metadata, index_dir=args.index_dir)

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    if args.index_dir == SEMANTIC_METADATA_UNWEIGHTED_INDEX_DIR:
        names = ("knowledge_chunks.json", "knowledge_embeddings.npy", "index_metadata.json")
    else:
        names = ("chunks.json", "embeddings.npy", "manifest.json")
    print(f"chunks_path: {args.index_dir / names[0]}")
    print(f"embeddings_path: {args.index_dir / names[1]}")
    print(f"metadata_path: {args.index_dir / names[2]}")


if __name__ == "__main__":
    main()
