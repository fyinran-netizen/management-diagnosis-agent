from __future__ import annotations


# def build_rewrite_messages(raw_query: str) -> list[dict[str, str]]:
#     """Build the dedicated prompt used to rewrite a retrieval query."""
#     return [
#         {
#             "role": "system",
#             "content": (
#                 "You rewrite management questions for knowledge retrieval. "
#                 "Return exactly one concise retrieval query as plain text. "
#                 "Keep the input language. Preserve every fact, constraint, and core intent. "
#                 "Remove conversational wording, repetition, and irrelevant expression. "
#                 "You may standardize management concepts already expressed by the user. "
#                 "Do not answer the question, diagnose the situation, infer causes, or add facts. "
#                 "Do not output labels, problem types, diagnosis hints, explanations, bullets, or quotation marks."
#             ),
#         },
#         {
#             "role": "user",
#             "content": f"/no_think\nRaw query:\n{raw_query}\n\nReturn only the rewritten retrieval query.",
#         },
#     ]


def build_rewrite_messages(raw_query: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You prepare user queries for knowledge retrieval. "
                "Make only minimal edits when necessary. "
                "If the original query is already clear and suitable for retrieval, return it unchanged. "
                "Preserve all important facts, symptoms, constraints, entities, and explicit concepts from the original query. "
                "Do not remove meaningful information. "
                "Do not infer, diagnose, explain, generalize, or introduce new management concepts. "
                "Do not translate the query. The output must use the same language as the input. "
                "Do not optimize for professional wording. Prefer wording close to the original query. "
                "Only remove obvious filler, repetition, or conversational noise. "
                "Return only one retrieval query as plain text."
            ),
        },
        {
            "role": "user",
            "content": f"/no_think\nRaw query:\n{raw_query}",
        },
    ]