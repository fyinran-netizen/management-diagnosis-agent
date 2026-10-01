from app.tools.ingestion import pipeline
from app.tools.ingestion.repositories import FilesystemArtifactRepository


def _write_fixture_corpus(tmp_path):
    sample_dir = tmp_path / "sample_knowledge_base"
    private_dir = tmp_path / "private_knowledge_base"
    (sample_dir).mkdir()
    (private_dir / "ch00").mkdir(parents=True)
    (private_dir / "ch01").mkdir(parents=True)

    (sample_dir / "01_sample.md").write_text(
        "# Sample knowledge\n\n## Core Idea\n\nSample content.\n",
        encoding="utf-8",
    )
    (private_dir / "ch00" / "s01.md").write_text(
        "# Preface\n\n## Preface\n\nThis must be skipped.\n",
        encoding="utf-8",
    )
    (private_dir / "ch01" / "s01.md").write_text(
        "# 第一章 企业的目的\n\n## Introduction\n\nPrivate content.\n",
        encoding="utf-8",
    )
    (private_dir / "_index.md").write_text(
        "# Index\n\nThis must not be loaded.\n",
        encoding="utf-8",
    )
    return sample_dir, private_dir


def test_load_knowledge_base_uses_canonical_sources_and_skips_private_preface(tmp_path, monkeypatch):
    sample_dir, private_dir = _write_fixture_corpus(tmp_path)
    monkeypatch.setattr(pipeline, "SAMPLE_KNOWLEDGE_DIR", sample_dir)
    monkeypatch.setattr(pipeline, "PRIVATE_KNOWLEDGE_DIR", private_dir)

    chunks = pipeline.IngestionPipeline(
        repository=FilesystemArtifactRepository(tmp_path / "artifacts")
    ).ingest(include_private=True).chunks

    assert {chunk.source for chunk in chunks} == {"ch00/s01.md", "ch01/s01.md"}
    assert "_index.md" not in {chunk.source for chunk in chunks}

    private_only = pipeline.IngestionPipeline(
        repository=FilesystemArtifactRepository(tmp_path / "private-only-artifacts")
    ).ingest(include_private=True, include_sample=False).chunks
    assert {chunk.source for chunk in private_only} == {"ch01/s01.md"}


def test_load_knowledge_base_excludes_private_when_disabled(tmp_path, monkeypatch):
    sample_dir, private_dir = _write_fixture_corpus(tmp_path)
    monkeypatch.setattr(pipeline, "SAMPLE_KNOWLEDGE_DIR", sample_dir)
    monkeypatch.setattr(pipeline, "PRIVATE_KNOWLEDGE_DIR", private_dir)

    chunks = pipeline.IngestionPipeline(
        repository=FilesystemArtifactRepository(tmp_path / "artifacts")
    ).ingest(include_private=False).chunks

    assert {chunk.source for chunk in chunks} == {"ch00/s01.md"}
