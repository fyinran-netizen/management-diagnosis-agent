from app.agent.prompts import format_retrieved_context


def test_format_retrieved_context_hides_raw_source_paths():
    context = format_retrieved_context(
        [
            {
                "source": "ch04/s06.md",
                "title": "Strategy and organization",
                "content": "Knowledge content",
            }
        ]
    )

    assert "Knowledge item 1" in context
    assert "Strategy and organization" in context
    assert "Knowledge content" in context
    assert "ch04/s06.md" not in context
    assert "Source:" not in context
