from scripts.enrich_semantic_metadata import normalize_metadata


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
