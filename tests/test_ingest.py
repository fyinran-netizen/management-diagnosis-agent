from pathlib import Path

from app.tools.retrieval import knowledge_loader


def test_load_knowledge_base_reads_nested_private_markdown(tmp_path, monkeypatch):
    sample_dir = tmp_path / "sample_knowledge_base"
    private_dir = tmp_path / "private_knowledge_base"
    preface_dir = private_dir / "ch00"
    nested_dir = private_dir / "ch01"

    sample_dir.mkdir()
    preface_dir.mkdir(parents=True)
    nested_dir.mkdir(parents=True)

    (sample_dir / "01_sample.md").write_text(
        "# 示例知识\n\n## Core Idea\n\n样例内容。\n",
        encoding="utf-8",
    )
    (preface_dir / "s01.md").write_text(
        "# 自序\n\n## 前言\n\n这部分不应该进入正文检索。\n",
        encoding="utf-8",
    )
    (nested_dir / "s01.md").write_text(
        "# 第一章 企业的目的\n\n## 引言\n\n顾客价值与新客户减少。\n",
        encoding="utf-8",
    )
    (private_dir / "_index.md").write_text(
        "# Index\n\n不应该被加载。\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(knowledge_loader, "SAMPLE_KNOWLEDGE_DIR", sample_dir)
    monkeypatch.setattr(knowledge_loader, "PRIVATE_KNOWLEDGE_DIR", private_dir)

    chunks = knowledge_loader.load_knowledge_base(include_private=True)

    sources = {chunk.source for chunk in chunks}
    titles = {chunk.title for chunk in chunks}
    contents = [chunk.content for chunk in chunks]

    assert "01_sample.md" in sources
    assert "ch01/s01.md" in sources
    assert "_index.md" not in sources
    assert "ch00/s01.md" not in sources
    assert "引言" in titles
    assert any("顾客价值与新客户减少" in content for content in contents)


def test_load_knowledge_base_skips_private_when_disabled(tmp_path, monkeypatch):
    sample_dir = tmp_path / "sample_knowledge_base"
    private_dir = tmp_path / "private_knowledge_base"
    nested_dir = private_dir / "ch01"

    sample_dir.mkdir()
    nested_dir.mkdir(parents=True)

    (sample_dir / "01_sample.md").write_text(
        "# 示例知识\n\n## Core Idea\n\n样例内容。\n",
        encoding="utf-8",
    )
    (nested_dir / "s01.md").write_text(
        "# 第一章 企业的目的\n\n## 引言\n\n顾客价值与新客户减少。\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(knowledge_loader, "SAMPLE_KNOWLEDGE_DIR", sample_dir)
    monkeypatch.setattr(knowledge_loader, "PRIVATE_KNOWLEDGE_DIR", private_dir)

    chunks = knowledge_loader.load_knowledge_base(include_private=False)

    sources = {chunk.source for chunk in chunks}

    assert "01_sample.md" in sources
    assert "ch01/s01.md" not in sources
