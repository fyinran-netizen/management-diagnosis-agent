from app.tools.ingestion.chunkers import chunk_source_sections, parse_source_sections


def test_chapter_intro_before_first_heading_gets_unique_section_id(tmp_path):
    lines = [
        "# 第八章 管理的终极回归",
        "",
        "章节导入内容。",
        "",
        "## 第一部分 系统思考",
        "",
        "第一部分正文。",
    ]

    sections = parse_source_sections(lines)
    source_ids = [chunk.source_id for chunk in chunk_source_sections(sections)]

    assert source_ids == ["ch08_s00_chunk_01", "ch08_s01_chunk_01"]
    assert len(source_ids) == len(set(source_ids))
