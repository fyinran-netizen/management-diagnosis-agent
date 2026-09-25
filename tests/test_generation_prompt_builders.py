from app.tools.generation.context import build_generation_context
from app.tools.generation.prompts import (
    build_core_diagnosis_prompt,
    build_management_concepts_prompt,
    build_recommendations_prompt,
    build_root_causes_prompt,
)


def test_all_section_prompt_builders_return_messages():
    context = build_generation_context(
        description="企业近期客户留存下降。",
        problem_types=["customer_value"],
        retrieved_chunks=[
            {
                "chapter_title": "Chapter",
                "section_title": "Section",
                "title": "Knowledge",
                "content": "Knowledge content",
            }
        ],
    )

    for builder in (
        build_core_diagnosis_prompt,
        build_management_concepts_prompt,
        build_root_causes_prompt,
        build_recommendations_prompt,
    ):
        messages = builder(context)
        assert len(messages) == 2
        assert {message["role"] for message in messages} == {"system", "user"}
