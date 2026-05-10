from __future__ import annotations

from pathlib import Path

from app.rag.chunker import TextChunk, split_markdown_by_headings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "sample_knowledge_base"
PRIVATE_KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "private_knowledge_base"


def iter_markdown_files(
    directory: Path,
    recursive: bool = False,
    skipped_top_level_dirs: set[str] | None = None,
) -> list[Path]:
    pattern = "**/*.md" if recursive else "*.md"
    paths = directory.glob(pattern)
    skipped_top_level_dirs = skipped_top_level_dirs or set()
    return sorted(
        path
        for path in paths
        if path.is_file()
        and not path.name.startswith("_")
        and (
            not skipped_top_level_dirs
            or path.relative_to(directory).parts[0] not in skipped_top_level_dirs
        )
    )


def load_chunks_from_path(path: Path, root_dir: Path) -> list[TextChunk]:
    chunks = split_markdown_by_headings(path)
    relative_source = path.relative_to(root_dir).as_posix()
    for chunk in chunks:
        chunk.source = relative_source
    return chunks


def load_knowledge_base(include_private: bool = False) -> list[TextChunk]:
    chunks: list[TextChunk] = []

    if SAMPLE_KNOWLEDGE_DIR.exists():
        for path in iter_markdown_files(SAMPLE_KNOWLEDGE_DIR):
            chunks.extend(load_chunks_from_path(path, SAMPLE_KNOWLEDGE_DIR))

    if include_private and PRIVATE_KNOWLEDGE_DIR.exists():
        for path in iter_markdown_files(
            PRIVATE_KNOWLEDGE_DIR,
            recursive=True,
            skipped_top_level_dirs={"ch00"},
        ):
            chunks.extend(load_chunks_from_path(path, PRIVATE_KNOWLEDGE_DIR))

    return chunks
