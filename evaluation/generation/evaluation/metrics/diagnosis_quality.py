"""Diagnosis quality metric configuration."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate the quality of the management diagnosis and reasoning in the generated report.",
    "Check whether the report identifies and formulates the central management problem clearly rather than merely restating surface symptoms.",
    "Check whether the analysis meaningfully distinguishes symptoms, contributing factors, and deeper root causes where such distinctions are appropriate.",
    "Evaluate whether the causal reasoning is coherent: the proposed causes should plausibly explain the observed problem, and the reasoning should show how the relevant factors connect.",
    "Check whether the report prioritizes the most important diagnostic issues rather than presenting an undifferentiated list of possible management concepts or causes.",
    "Check whether recommendations follow logically from the diagnosis: the proposed actions should address the causes or mechanisms identified in the analysis.",
    "Evaluate whether recommendations are sufficiently specific and practical to guide action while remaining appropriate to the level of information available.",
    "Penalize generic management advice, disconnected recommendation lists, symptom-level fixes presented as root-cause solutions, or recommendations that do not follow from the diagnosis.",
    "Do not penalize a diagnosis merely because it relies on a reasonable hypothesis or because a recommendation is not explicitly stated in the user input; evidential grounding belongs primarily to Faithfulness.",
    "Do not independently penalize unsupported facts, invented numbers, or uncertainty calibration unless they materially damage the coherence or usefulness of the diagnosis; those issues are evaluated primarily by Faithfulness.",
    "A perfect score should represent a diagnosis that clearly identifies the management problem, develops a coherent explanation of its causes, prioritizes the important mechanisms, and derives practical recommendations from that reasoning."
]


def build_metric(model):
    """Build the diagnosis quality GEval metric with the shared project judge."""
    return GEval(
        name="Diagnosis Quality",
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.RETRIEVAL_CONTEXT,
        ],
        evaluation_steps=EVALUATION_STEPS,
        model=model,
        async_mode=False,
    )
