from app.tools.generation.prompts.common import build_section_messages
from app.tools.generation.schemas import GenerationContext


def build_recommendations_prompt(context: GenerationContext) -> list[dict[str, str]]:
    return build_section_messages(
        context,
        "recommendations",
        """
Use core_diagnosis and root_causes as the basis for concrete action. Give several
prioritized recommendations that correspond to the mechanisms already identified,
covering the main intervention points rather than one broad slogan. Write the action
itself directly: specify what management should change, establish, review, stop, test,
or coordinate, and indicate the immediate object or direction of the action. Where
useful, include a practical sequence or a way to check whether the adjustment is
working, but do not invent targets, resources, or company facts not provided.

Use retrieved knowledge to make the actions substantive, while expressing them as
normal case-specific recommendations rather than saying “可借鉴”“可参考” or naming
an external idea as a substitute for the recommendation. If information is missing,
state a condition and then give the action under that condition. Do not merely repeat
the diagnosis or root-cause explanation. Include at least three distinct action items
when the available evidence supports them, and make each item concrete enough to be
acted on without consulting the retrieved context again. Separate the action items into
clear sentences, with each sentence naming one adjustment object and one action; do
not merge all actions into a single vague sentence.
""".strip(),
    )
