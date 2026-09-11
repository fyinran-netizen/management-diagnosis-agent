"""Custom faithfulness metric for management diagnosis generation."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate whether the generated report is faithful to the evidence available in the user input and retrieval context.",
    "Distinguish between: facts explicitly stated in the user input, general management knowledge from the retrieval context, and hypotheses inferred by the generated report.",
    "Do not penalize the report for omitting information from the retrieval context. Missing a knowledge point is not a faithfulness error.",
    "Penalize claims about the specific company when they are presented as confirmed facts but are only hypotheses or general management possibilities.",
    "Penalize invented or unsupported numerical values, percentages, thresholds, causal relationships, operational conditions, or company-specific facts.",
    "Penalize conclusions that are stronger or more certain than the evidence supports, such as turning a possible cause into a confirmed root cause.",
    "General management principles from the retrieval context may support recommendations or hypotheses, but they do not by themselves prove that the specific company has that condition.",
    "Do not penalize reasonable wording differences or synthesis when the underlying meaning is supported by the available evidence.",
    "A perfect score should require that all meaningful factual and causal claims are supported by the input or retrieval context, with uncertainty handled appropriately.",
]


def build_metric(model):
    """Build the custom faithfulness GEval metric."""
    return GEval(
        name="Faithfulness",
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.RETRIEVAL_CONTEXT,
        ],
        evaluation_steps=EVALUATION_STEPS,
        model=model,
        async_mode=False,
    )