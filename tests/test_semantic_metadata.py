from scripts.enrich_semantic_metadata import (
    ENGLISH_DIAGNOSIS_TAGS,
    build_prompt,
    normalize_metadata,
)


def test_build_prompt_separates_stable_contract_from_chunk_data():
    messages = build_prompt(
        {
            "source_id": "ch01-sec02-chunk01",
            "chapter_title": "战略",
            "section_title": "客户价值",
            "title": "不要把指标当目标",
        },
        "正文中的管理观点。",
    )

    assert [message["role"] for message in messages] == ["system", "user"]

    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]

    assert "输出契约" in system_prompt
    assert '"diagnosis_tags": []' in system_prompt
    assert "正文中的管理观点。" not in system_prompt
    assert "ch01-sec02-chunk01" not in system_prompt

    assert "<source_context>" in user_prompt
    assert "<cleaned_content>\n正文中的管理观点。\n</cleaned_content>" in user_prompt
    assert "输出契约" not in user_prompt
    assert "Rules:" not in user_prompt
    assert all(tag not in user_prompt for tag in ENGLISH_DIAGNOSIS_TAGS)


def test_normalize_metadata_keeps_chinese_labels_and_filters_english_tags():
    result = normalize_metadata(
        {
            "summary": "企业把指标当目标，导致客户价值被牺牲。",
            "extracted": {
                "concept_keywords": ["客户价值", "指标体系"],
                "method_keywords": ["目标校准"],
                "definition_phrases": ["指标应服务于目标"],
                "named_entities": ["德鲁克"],
            },
            "inferred": {
                "symptom_keywords": ["只看KPI", "复购下降"],
                "diagnosis_labels_zh": ["指标体系错位", "客户价值错位"],
                "diagnosis_tags": ["metrics_misalignment", "not_allowed"],
                "recommended_methods": ["重构指标体系"],
            },
        }
    )

    assert result["extracted"]["definition_phrases"] == ["指标应服务于目标"]
    assert result["inferred"]["diagnosis_labels_zh"] == ["指标体系错位", "客户价值错位"]
    assert result["inferred"]["diagnosis_tags"] == ["metrics_misalignment"]
