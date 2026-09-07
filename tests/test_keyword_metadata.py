from types import SimpleNamespace

from app.tools.retrieval.retrievers.bm25 import (
    SEMANTIC_METADATA_PATH,
    build_bm25_document_text,
    get_cached_bm25_index,
    semantic_metadata_to_search_text,
)


def test_semantic_metadata_to_search_text_uses_keyword_fields_and_skips_noise():
    record = {
        "summary": "short summary",
        "extracted": {
            "concept_keywords": ["customer value"],
            "method_keywords": ["market test"],
            "definition_phrases": ["long definition should not be indexed"],
            "named_entities": ["Drucker"],
        },
        "inferred": {
            "symptom_keywords": ["growth slowdown"],
            "diagnosis_labels_zh": ["customer value mismatch"],
            "diagnosis_tags": ["customer_value_misalignment"],
            "recommended_methods": ["customer interview"],
        },
        "quality": {"metadata_confidence": 0.9},
    }

    text = semantic_metadata_to_search_text(record)

    assert "short summary" in text
    assert text.count("growth slowdown") == 3
    assert text.count("customer_value_misalignment") == 3
    assert "long definition should not be indexed" not in text
    assert "metadata_confidence" not in text

    unweighted = semantic_metadata_to_search_text(record, weighted=False)
    assert unweighted.count("growth slowdown") == 1
    assert unweighted.count("customer_value_misalignment") == 1


def test_bm25_metadata_path_is_fixed_and_modes_build_distinct_indexes():
    assert SEMANTIC_METADATA_PATH.as_posix().endswith(
        "data/private_knowledge_base/semantic_metadata.jsonl"
    )
    assert get_cached_bm25_index("base") is not get_cached_bm25_index("weighted")
    assert get_cached_bm25_index("unweighted") is not get_cached_bm25_index("weighted")
    assert get_cached_bm25_index.__wrapped__.__defaults__ == ("unweighted",)


def test_build_bm25_document_text_includes_structural_and_semantic_text():
    chunk = SimpleNamespace(
        chapter_title="chapter",
        section_title="section",
        title="title",
        content="body",
    )

    text = build_bm25_document_text(chunk, "symptom tag")

    assert "chapter" in text
    assert "section" in text
    assert text.count("title") == 2
    assert "body" in text
    assert "symptom tag" in text
