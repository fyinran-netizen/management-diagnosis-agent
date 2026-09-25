from app.tools.generation.prompts.common import build_section_messages
from app.tools.generation.schemas import GenerationContext


def build_core_diagnosis_prompt(context: GenerationContext) -> list[dict[str, str]]:
    return build_section_messages(
        context,
        "core_diagnosis",
        """
Write the central management diagnosis as a coherent analytical passage, not as a
label or a list of retrieved concepts. Start from the user's stated symptoms and
explain the upstream management problem, misalignment, or tension that best connects
them. Make clear what is observed versus what is inferred, using conditional language
for the latter. Integrate relevant retrieved knowledge only where it sharpens this
diagnosis.

Keep the scope to the most important one or two connected diagnoses. Explain the
management-level meaning and its link to the surface symptoms, but leave the detailed
causal chain for root_causes. Do not explain management concepts one by one and do
not provide recommendations. Write enough connected sentences to form a complete
diagnosis passage; do not answer with a single slogan or a source summary.
""".strip(),
    )
