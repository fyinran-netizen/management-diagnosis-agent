from __future__ import annotations

from pathlib import Path

from app.core.config import PRIVATE_KNOWLEDGE_DIR, SAMPLE_KNOWLEDGE_DIR
from app.tools.ingestion.chunkers.section_based import SectionBasedChunker
from app.tools.ingestion.loaders.markdown import MarkdownLoader
from app.tools.ingestion.metadata import SemanticMetadataProvider, SourceMetadataBuilder
from app.tools.ingestion.repositories import FilesystemArtifactRepository
from app.tools.ingestion.schemas import IngestionResult


def iter_markdown_files(directory: Path, recursive: bool = False, skipped_top_level_dirs: set[str] | None = None) -> list[Path]:
    paths = directory.glob("**/*.md" if recursive else "*.md")
    skipped = skipped_top_level_dirs or set()
    return sorted(p for p in paths if p.is_file() and not p.name.startswith("_") and (not skipped or p.relative_to(directory).parts[0] not in skipped))


class IngestionPipeline:
    def __init__(self, *, loader=None, chunker=None, semantic_provider: SemanticMetadataProvider | None = None, repository=None):
        self.loader = loader or MarkdownLoader()
        self.chunker = chunker or SectionBasedChunker()
        self.repository = repository or FilesystemArtifactRepository()
        self.source_metadata_builder = SourceMetadataBuilder()
        self.semantic_provider = semantic_provider

    def ingest(self, *, include_private: bool = False, include_sample: bool = True, input_paths: list[Path] | None = None, persist: bool = True) -> IngestionResult:
        if input_paths is None and self.repository.has_corpus():
            return IngestionResult(
                chunks=self.repository.load_chunks(),
                source_metadata=self.repository.load_source_metadata(),
                semantic_metadata=self.repository.load_semantic_metadata(),
                skipped=True,
                reason="existing_corpus",
            )
        paths: list[tuple[Path, Path]] = []
        if input_paths:
            for path in input_paths:
                path = path.resolve()
                root = path.parent
                for candidate in (PRIVATE_KNOWLEDGE_DIR, SAMPLE_KNOWLEDGE_DIR):
                    try:
                        path.relative_to(candidate)
                        root = candidate
                        break
                    except ValueError:
                        continue
                paths.append((path, root))
        else:
            if include_sample and SAMPLE_KNOWLEDGE_DIR.exists():
                paths.extend((p, SAMPLE_KNOWLEDGE_DIR) for p in iter_markdown_files(SAMPLE_KNOWLEDGE_DIR))
            if include_private and PRIVATE_KNOWLEDGE_DIR.exists():
                paths.extend((p, PRIVATE_KNOWLEDGE_DIR) for p in iter_markdown_files(PRIVATE_KNOWLEDGE_DIR, True, {"ch00"}))
        documents = [self.loader.load(path, root_dir=root) for path, root in paths]
        chunks = [chunk for document in documents for chunk in self.chunker.chunk(document)]
        source_metadata = self.source_metadata_builder.build(chunks)
        semantic_metadata = self.semantic_provider.get(chunks) if self.semantic_provider else []
        if input_paths and persist:
            self.repository.save_chunks(chunks)
            self.repository.save_source_metadata(source_metadata)
            if semantic_metadata:
                self.repository.save_semantic_metadata(semantic_metadata)
        return IngestionResult(
            documents=documents,
            chunks=chunks,
            source_metadata=source_metadata,
            semantic_metadata=semantic_metadata,
        )


def ingest_knowledge_base(*, include_private: bool = False, include_sample: bool = True, input_paths: list[Path] | None = None, persist: bool = True) -> IngestionResult:
    return IngestionPipeline().ingest(include_private=include_private, include_sample=include_sample, input_paths=input_paths, persist=persist)
