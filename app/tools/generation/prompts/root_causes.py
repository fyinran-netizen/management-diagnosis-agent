from app.tools.generation.prompts.common import build_section_messages
from app.tools.generation.schemas import GenerationContext


def build_root_causes_prompt(context: GenerationContext) -> list[dict[str, str]]:
    return build_section_messages(
        context,
        "root_causes",
        """
Use core_diagnosis as the starting point and explain why the situation may have
developed. Build a connected causal analysis across at least two or three layers, such
as management choices or priorities, incentives and measurement, organizational
processes or coordination, and resulting employee or customer responses. Show the
links between these layers and the observed symptoms instead of producing unrelated
cause labels.

Clearly separate what the user explicitly states from what is a reasonable inference
drawn from the retrieved knowledge. Phrase unverified mechanisms as possibilities and
do not invent company-specific facts. Use retrieved knowledge to explain the mechanism
behind the case, not to paste together quotations or named fragments. Do not provide
recommendations or action steps. Produce a sufficiently developed passage with at least
three linked causal steps or layers; do not compress the analysis into one or two
generic labels. Do not copy the wording or conclusion of core_diagnosis. Each sentence
should answer a different “why” question and advance the causal chain from a possible
management condition to an organizational response and then to the observed outcome.
""".strip(),
    )
