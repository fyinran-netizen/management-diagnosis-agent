"""Run a chunking strategy through corpus, vector-index, and retrieval evaluation.

The strategy implementation remains in app.tools.ingestion.  This script only
coordinates existing ingestion, vector-index, and benchmark entry points.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import PRIVATE_KNOWLEDGE_DIR
from app.tools.ingestion.chunkers import SectionBasedChunker
from app.tools.ingestion.loaders import MarkdownLoader
from app.tools.ingestion.metadata import SourceMetadataBuilder
from app.tools.ingestion.repositories import FilesystemArtifactRepository
from app.tools.retrieval.vector_store import BASE_VECTOR_INDEX_DIR


DEFAULT_EXPERIMENT_ROOT = PROJECT_ROOT / "data" / "chunking_strategy_experiments"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "evaluation" / "chunking"
DEFAULT_SOURCE = PROJECT_ROOT / "source_docs" / "raw_converted.md"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


def build_experiment_corpus(source_path: Path, corpus_dir: Path) -> int:
    document = MarkdownLoader().load(source_path, root_dir=source_path.parent)
    chunks = SectionBasedChunker().chunk(document)
    # The existing retrieval baseline is private corpus scope excluding ch00;
    # keep this experiment corpus identical to that scope.
    chunks = [chunk for chunk in chunks if chunk.chapter_id != "ch00"]
    repository = FilesystemArtifactRepository(corpus_dir)
    repository.save_chunks(chunks)
    repository.save_source_metadata(SourceMetadataBuilder().build(chunks))
    return len(chunks)


def run_command(command: list[str], env: dict[str, str]) -> str:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.stdout


def output_path(output: str, label: str) -> Path:
    match = re.search(rf"^{label}: (.+)$", output, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find {label} in command output")
    return Path(match.group(1).strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the section_based chunking experiment pipeline.")
    parser.add_argument("--strategy", choices=("section_based",), default="section_based")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--experiment-root", type=Path, default=DEFAULT_EXPERIMENT_ROOT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    corpus_dir = args.experiment_root / args.strategy / "corpus"
    index_dir = args.experiment_root / args.strategy / "vector_index"
    args.report_dir.mkdir(parents=True, exist_ok=True)
    chunk_count = build_experiment_corpus(args.source.resolve(), corpus_dir)
    print(f"experiment: {args.strategy}")
    print(f"corpus_dir: {corpus_dir}")
    print(f"generated_chunks: {chunk_count}")

    env = os.environ.copy()
    env["EMBEDDING_MODEL"] = EMBEDDING_MODEL
    build_output = run_command(
        [
            sys.executable,
            "scripts/build_vector_index.py",
            "--corpus-dir",
            str(corpus_dir),
            "--index-dir",
            str(index_dir),
            "--metadata-mode",
            "base",
            "--batch-size",
            str(args.batch_size),
        ],
        env,
    )
    index_manifest = index_dir / "manifest.json"
    vector_count_match = re.search(r'"chunk_count": (\d+)', build_output)
    vector_count = int(vector_count_match.group(1)) if vector_count_match else chunk_count
    print(f"vector_index_dir: {index_dir}")
    print(f"vector_count: {vector_count}")

    benchmark_output = run_command(
        [
            sys.executable,
            "scripts/run_retrieval_benchmark.py",
            "--corpus-dir",
            str(corpus_dir),
            "--index-dir",
            str(index_dir),
            "--report-dir",
            str(args.report_dir),
            "--experiments",
            str(args.report_dir / "experiments.jsonl"),
            "--bm25-metadata-mode",
            "base",
            "--top-k",
            "20",
            "--methods",
            "bm25",
            "embedding",
            "linear_hybrid",
        ],
        env,
    )
    print(f"report_json: {output_path(benchmark_output, 'report')}")
    print(f"report_markdown: {output_path(benchmark_output, 'markdown')}")
    print(f"index_manifest: {index_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
