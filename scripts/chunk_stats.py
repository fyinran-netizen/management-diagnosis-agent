from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

from app.tools.retrieval.knowledge_loader import PRIVATE_KNOWLEDGE_DIR, SAMPLE_KNOWLEDGE_DIR, iter_markdown_files, load_chunks_from_path


EXCLUDED_SOURCES = {"99_private_test.md"}


def load_stat_chunks(include_sample: bool) -> list:
    chunks = []
    if include_sample and SAMPLE_KNOWLEDGE_DIR.exists():
        for path in iter_markdown_files(SAMPLE_KNOWLEDGE_DIR):
            chunks.extend(load_chunks_from_path(path, SAMPLE_KNOWLEDGE_DIR))

    if PRIVATE_KNOWLEDGE_DIR.exists():
        for path in iter_markdown_files(
            PRIVATE_KNOWLEDGE_DIR,
            recursive=True,
            skipped_top_level_dirs={"ch00"},
        ):
            chunks.extend(load_chunks_from_path(path, PRIVATE_KNOWLEDGE_DIR))

    return [chunk for chunk in chunks if chunk.source not in EXCLUDED_SOURCES]


def build_stats(include_sample: bool, preview_chars: int) -> list[dict[str, object]]:
    chunks = load_stat_chunks(include_sample=include_sample)
    rows: list[dict[str, object]] = []

    for index, chunk in enumerate(chunks, start=1):
        content = chunk.content.strip()
        rows.append(
            {
                "index": index,
                "source": chunk.source,
                "title": chunk.title,
                "char_count": len(content),
                "line_count": len(content.splitlines()),
                "preview": " ".join(content.split())[:preview_chars],
            }
        )

    return rows


def print_table(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("No chunks found.")
        return

    print(f"chunks: {len(rows)}")
    print(f"min_chars: {min(row['char_count'] for row in rows)}")
    print(f"max_chars: {max(row['char_count'] for row in rows)}")
    print(f"avg_chars: {sum(row['char_count'] for row in rows) // len(rows)}")
    print()
    print("| index | chars | lines | source | title | preview |")
    print("| --- | ---: | ---: | --- | --- | --- |")
    for row in rows:
        preview = str(row["preview"]).replace("|", "\\|")
        title = str(row["title"]).replace("|", "\\|")
        print(
            f"| {row['index']} | {row['char_count']} | {row['line_count']} | "
            f"{row['source']} | {title} | {preview} |"
        )


def write_json(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["index", "source", "title", "char_count", "line_count", "preview"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show RAG chunk statistics.")
    parser.add_argument(
        "--include-sample",
        action="store_true",
        help="Also include sample knowledge chunks. The default stats are private knowledge only.",
    )
    parser.add_argument("--preview-chars", type=int, default=80)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    args = parser.parse_args()

    rows = build_stats(include_sample=args.include_sample, preview_chars=args.preview_chars)
    print_table(rows)

    if args.json_out:
        write_json(args.json_out, rows)
        print(f"\njson_out: {args.json_out}")
    if args.csv_out:
        write_csv(args.csv_out, rows)
        print(f"csv_out: {args.csv_out}")


if __name__ == "__main__":
    main()
