from app.tools.generation.prompts.common import build_section_messages
from app.tools.generation.schemas import GenerationContext


def build_management_concepts_prompt(context: GenerationContext) -> list[dict[str, str]]:
    return build_section_messages(
        context,
        "management_concepts",
        """
Use core_diagnosis only as the scope boundary. Explain two or three management
concepts that directly illuminate that diagnosis. For each concept, state its meaning
in plain Chinese and then explain what aspect of this case it helps interpret. The
concepts may come from the retrieved knowledge, but weave them into an explanation
rather than naming a string of theories or repeating source wording.

This section is about “what the relevant concepts mean and why they matter here”. Give
each selected concept its own explanatory sentence or clause so the section contains
actual concept explanation, not another diagnosis paragraph. Do
not restate the core diagnosis or list its symptoms as the main content. Do not use
the concept section to claim that one factor caused another; leave causal sequence and
mechanisms for root_causes. Do not provide recommendations. If a concept does not
clearly clarify the supplied diagnosis, leave it out. Prefer two or three distinct
concepts, each with a definition followed by its specific interpretive relevance.
""".strip(),
    )
