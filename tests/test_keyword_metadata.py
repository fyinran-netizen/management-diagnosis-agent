from types import SimpleNamespace

from app.rag.retrieval.keyword_retriever import (
    build_bm25_document_text,
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
