from scripts.merge_semantic_tags import merge_diagnosis_tags, merge_records


METRICS_LABEL = "\u6307\u6807\u4f53\u7cfb\u9519\u4f4d"
STRATEGY_LABEL = "\u6218\u7565\u6267\u884c\u8131\u8282"
UNKNOWN_LABEL = "\u7ec4\u7ec7\u534f\u540c\u5931\u6548"


def test_merge_diagnosis_tags_maps_known_labels_and_dedupes_tags():
    original = {
        "source_id": "ch01_s01_chunk_01",
        "inferred": {
            "diagnosis_labels_zh": [
                METRICS_LABEL,
                STRATEGY_LABEL,
                METRICS_LABEL,
                UNKNOWN_LABEL,
            ],
            "diagnosis_tags": ["metrics_misalignment", "not_allowed"],
        },
    }

    result = merge_diagnosis_tags(original)

    assert result.record["inferred"]["diagnosis_tags"] == [
        "metrics_misalignment",
        "strategy_execution_gap",
    ]
    assert result.mapped_labels == [METRICS_LABEL, STRATEGY_LABEL]
    assert result.unmapped_labels == [UNKNOWN_LABEL]
    assert original["inferred"]["diagnosis_tags"] == ["metrics_misalignment", "not_allowed"]


def test_merge_records_can_limit_to_pending_records():
    records = [
        {
            "source_id": "pending",
            "review": {"status": "pending"},
            "inferred": {"diagnosis_labels_zh": [METRICS_LABEL], "diagnosis_tags": []},
        },
        {
            "source_id": "needs-edit",
            "review": {"status": "needs_edit"},
            "inferred": {"diagnosis_labels_zh": [STRATEGY_LABEL], "diagnosis_tags": []},
        },
    ]

    merged, results = merge_records(records, pending_only=True)

    assert len(results) == 1
    assert merged[0]["inferred"]["diagnosis_tags"] == ["metrics_misalignment"]
    assert merged[1]["inferred"]["diagnosis_tags"] == []
