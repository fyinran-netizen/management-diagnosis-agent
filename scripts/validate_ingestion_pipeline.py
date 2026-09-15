"""Validate ingestion artifacts and compare the current chunking pipeline to them.

This is intentionally an orchestration-only script.  Parsing, loading, chunking,
metadata construction, and artifact reading are delegated to app.tools.ingestion.
It never persists chunks or semantic metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.ingestion.chunkers import SectionBasedChunker
from app.tools.ingestion.loaders import MarkdownLoader
from app.tools.ingestion.metadata import SourceMetadataBuilder
from app.tools.ingestion.metadata.semantic import ENGLISH_DIAGNOSIS_TAGS
from app.tools.ingestion.repositories import FilesystemArtifactRepository
from app.core.config import PRIVATE_KNOWLEDGE_DIR


PARITY_FIELDS = (
    "path",
    "source_id",
    "chapter_id",
    "section_id",
    "chunk_index",
    "chunk_count",
    "title",
    "content",
    "char_count",
)
NESTED_TYPES = {
    "extracted": dict,
    "inferred": dict,
    "evidence_spans": list,
    "quality": dict,
    "review": dict,
    "generation": dict,
}
LIST_FIELDS = {
    ("extracted", key)
    for key in ("concept_keywords", "method_keywords", "definition_phrases", "named_entities")
} | {
    ("inferred", key)
    for key in ("symptom_keywords", "diagnosis_labels_zh", "diagnosis_tags", "recommended_methods")
}


def _ids(records: list[dict[str, Any]]) -> list[Any]:
    return [record.get("source_id") for record in records]


def _duplicates(values: list[Any]) -> list[Any]:
    return sorted({value for value, count in Counter(values).items() if value is not None and count > 1})


def _chunk_fields(chunk: Any, source_id: Any = None) -> dict[str, Any]:
    return {
        "path": chunk.source,
        "source_id": source_id if source_id is not None else chunk.source_id,
        "chapter_id": chunk.chapter_id,
        "section_id": chunk.section_id,
        "chunk_index": chunk.chunk_index,
        "chunk_count": chunk.chunk_count,
        "title": chunk.title,
        "content": chunk.content,
        "char_count": len(chunk.content),
    }


def validate_corpus(repository: FilesystemArtifactRepository) -> dict[str, Any]:
    source_metadata = repository.load_source_metadata()
    semantic_path = repository.root / "semantic_metadata.jsonl"
    semantic_parse_error = None
    try:
        semantic_metadata = repository.load_semantic_metadata()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        semantic_metadata = []
        semantic_parse_error = str(exc)

    missing_paths: list[str] = []
    for record in source_metadata:
        path_value = record.get("path")
        if not isinstance(path_value, str) or not (repository.root / path_value).is_file():
            missing_paths.append(str(path_value))

    load_error = None
    loaded_chunks = []
    try:
        loaded_chunks = repository.load_chunks()
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        load_error = str(exc)

    manifest_paths = {record.get("path") for record in source_metadata}
    loaded_paths = {chunk.source for chunk in loaded_chunks}
    failed_chunk_loads = sorted(str(path) for path in manifest_paths - loaded_paths if path is not None)
    manifest_by_path = {record.get("path"): record for record in source_metadata}
    chunk_source_mismatches = sorted(
        chunk.source
        for chunk in loaded_chunks
        if manifest_by_path.get(chunk.source, {}).get("source_id") != chunk.source_id
    )

    corpus_ids = set(_ids(source_metadata))
    semantic_ids = _ids(semantic_metadata)
    invalid_tags: list[dict[str, Any]] = []
    nested_type_errors: list[str] = []
    for record in semantic_metadata:
        source_id = record.get("source_id")
        for field, expected in NESTED_TYPES.items():
            if field in record and not isinstance(record[field], expected):
                nested_type_errors.append(f"{source_id}: {field} must be {expected.__name__}")
        for parent, field in LIST_FIELDS:
            value = record.get(parent, {}).get(field) if isinstance(record.get(parent), dict) else None
            if value is not None and not isinstance(value, list):
                nested_type_errors.append(f"{source_id}: {parent}.{field} must be list")
        evidence = record.get("evidence_spans")
        if isinstance(evidence, list):
            for index, item in enumerate(evidence):
                if not isinstance(item, dict):
                    nested_type_errors.append(f"{source_id}: evidence_spans[{index}] must be object")
        tags = record.get("inferred", {}).get("diagnosis_tags") if isinstance(record.get("inferred"), dict) else None
        if tags is not None:
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                nested_type_errors.append(f"{source_id}: inferred.diagnosis_tags must be list[str]")
            else:
                bad = sorted(set(tags) - set(ENGLISH_DIAGNOSIS_TAGS))
                if bad:
                    invalid_tags.append({"source_id": source_id, "tags": bad})

    return {
        "source_metadata": source_metadata,
        "semantic_metadata": semantic_metadata,
        "loaded_chunks": loaded_chunks,
        "missing_paths": missing_paths,
        "failed_chunk_loads": failed_chunk_loads,
        "chunk_source_mismatches": chunk_source_mismatches,
        "duplicate_source_ids": _duplicates(_ids(source_metadata)),
        "semantic_duplicates": _duplicates(semantic_ids),
        "orphan_semantic": sorted(str(value) for value in set(semantic_ids) - corpus_ids if value is not None),
        "missing_semantic": sorted(str(value) for value in corpus_ids - set(semantic_ids) if value is not None),
        "semantic_parse_error": semantic_parse_error if semantic_path.exists() else "file missing",
        "nested_type_errors": nested_type_errors,
        "invalid_tags": invalid_tags,
        "load_error": load_error,
    }


def validate_parity(
    source_path: Path,
    golden_metadata: list[dict[str, Any]],
    golden_chunks: list[Any],
) -> dict[str, Any]:
    loader = MarkdownLoader()
    chunker = SectionBasedChunker()
    builder = SourceMetadataBuilder()
    document = loader.load(source_path, root_dir=source_path.parent)
    generated_chunks = chunker.chunk(document)
    generated_metadata = builder.build(generated_chunks)
    generated = [_chunk_fields(chunk, record.get("source_id")) for chunk, record in zip(generated_chunks, generated_metadata)]

    golden_by_id = {record.get("source_id"): dict(record) for record in golden_metadata}
    golden_chunks_by_id = {chunk.source_id: chunk for chunk in golden_chunks}
    for source_id, chunk in golden_chunks_by_id.items():
        golden_by_id.setdefault(source_id, {})["content"] = chunk.content
    generated_by_id: dict[Any, list[dict[str, Any]]] = {}
    for item in generated:
        generated_by_id.setdefault(item["source_id"], []).append(item)
    missing = sorted(set(golden_by_id) - set(generated_by_id))
    extra = sorted(set(generated_by_id) - set(golden_by_id))
    metadata_mismatches: list[dict[str, Any]] = []
    content_mismatches: list[dict[str, Any]] = []
    for source_id in sorted(set(golden_by_id) & set(generated_by_id)):
        actual = generated_by_id[source_id][0]
        expected = golden_by_id[source_id]
        differences = [
            field
            for field in PARITY_FIELDS
            if field in expected and actual.get(field) != expected.get(field)
        ]
        if differences:
            summary = {"source_id": source_id, "fields": differences}
            if "content" in differences:
                content_mismatches.append(summary)
            else:
                metadata_mismatches.append(summary)
    exact_matches = sum(
        1
        for item in generated
        if item.get("source_id") in golden_by_id
        and all(
            field in golden_by_id[item["source_id"]]
            and item.get(field) == golden_by_id[item["source_id"]].get(field)
            for field in PARITY_FIELDS
        )
    )
    return {
        "generated": generated,
        "generated_count": len(generated),
        "golden_count": len(golden_metadata),
        "exact_matches": exact_matches,
        "missing": missing,
        "extra": extra,
        "metadata_mismatches": metadata_mismatches,
        "content_mismatches": content_mismatches,
    }


def _print_mismatch(label: str, items: list[dict[str, Any]], limit: int = 10) -> None:
    if items:
        print(f"{label}: " + ", ".join(f"{item['source_id']} ({','.join(item['fields'])})" for item in items[:limit]))


def _print_id_sample(label: str, values: list[Any], limit: int = 10) -> None:
    if values:
        suffix = " ..." if len(values) > limit else ""
        print(f"  {label}: {', '.join(str(value) for value in values[:limit])}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=PRIVATE_KNOWLEDGE_DIR)
    parser.add_argument("--source", type=Path, default=PROJECT_ROOT / "source_docs/raw_converted.md")
    args = parser.parse_args()

    repository = FilesystemArtifactRepository(args.corpus)
    corpus = validate_corpus(repository)
    parity = validate_parity(args.source, corpus["source_metadata"], corpus["loaded_chunks"])
    semantic_ok = not any((corpus["semantic_parse_error"], corpus["semantic_duplicates"], corpus["orphan_semantic"], corpus["missing_semantic"], corpus["invalid_tags"], corpus["nested_type_errors"]))
    corpus_ok = not any((corpus["missing_paths"], corpus["failed_chunk_loads"], corpus["chunk_source_mismatches"], corpus["duplicate_source_ids"], corpus["load_error"]))
    parity_ok = not any((parity["missing"], parity["extra"], parity["metadata_mismatches"], parity["content_mismatches"])) and parity["generated_count"] == parity["golden_count"]

    print("Existing corpus:")
    print(f"- chunks: {len(corpus['loaded_chunks'])}")
    print(f"- source metadata: {len(corpus['source_metadata'])}")
    print(f"- semantic metadata: {len(corpus['semantic_metadata'])}")
    print(f"- missing paths: {len(corpus['missing_paths'])}")
    print(f"- duplicate source_ids: {len(corpus['duplicate_source_ids'])}")
    print(f"- orphan semantic metadata: {len(corpus['orphan_semantic'])}")
    print(f"- failed chunk loads: {len(corpus['failed_chunk_loads'])}")
    print(f"- chunk/source_id mismatches: {len(corpus['chunk_source_mismatches'])}")
    print("\nChunking parity:")
    print(f"- generated chunks: {parity['generated_count']}")
    print(f"- golden chunks: {parity['golden_count']}")
    print(f"- exact matches: {parity['exact_matches']}")
    print(f"- missing: {len(parity['missing'])}")
    print(f"- extra: {len(parity['extra'])}")
    print(f"- metadata mismatches: {len(parity['metadata_mismatches'])}")
    print(f"- content mismatches: {len(parity['content_mismatches'])}")
    _print_id_sample("missing source_ids", parity["missing"])
    _print_id_sample("extra source_ids", parity["extra"])
    _print_mismatch("  mismatch details", parity["metadata_mismatches"] + parity["content_mismatches"])
    print("\nSemantic metadata integrity:")
    print(f"- parsed: {'yes' if corpus['semantic_parse_error'] is None else 'no'}")
    print(f"- duplicates: {len(corpus['semantic_duplicates'])}")
    print(f"- missing: {len(corpus['missing_semantic'])}")
    print(f"- orphan: {len(corpus['orphan_semantic'])}")
    print(f"- invalid tags: {len(corpus['invalid_tags'])}")
    print(f"- nested type errors: {len(corpus['nested_type_errors'])}")
    print(f"\nResult: corpus={'PASS' if corpus_ok else 'FAIL'}, parity={'PASS' if parity_ok else 'FAIL'}, semantic={'PASS' if semantic_ok else 'FAIL'}")
    return 0 if corpus_ok and parity_ok and semantic_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
