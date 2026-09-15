"""Diagnosis quality metric configuration."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate the overall quality of the management diagnosis, not merely whether the report contains diagnosis, root-cause, and recommendation sections.",
    "Assess whether the report identifies the central management problem and develops a coherent explanation that goes meaningfully beyond restating the observed symptoms.",
    "Assess whether the proposed causes form a plausible and prioritized explanation of the problem, rather than a collection of generally relevant management concepts.",
    "Assess whether the recommendations follow from the diagnosed mechanisms and would meaningfully address them, rather than being broadly useful but loosely connected management advice.",
    "Judge the diagnosis as a whole for explanatory depth, internal coherence, prioritization, and practical usefulness. Evidential support and factual grounding are evaluated separately by Faithfulness."
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
