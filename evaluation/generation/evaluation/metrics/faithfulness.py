"""Custom faithfulness metric for management diagnosis generation."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate whether the generated report remains faithful to the evidence available in the user input and retrieval context.",
    "Distinguish among company-specific facts from the user input, general management knowledge from the retrieval context, and hypotheses or interpretations introduced by the report.",
    "Check whether meaningful factual, causal, numerical, and company-specific claims are supported by the available evidence, while allowing retrieval knowledge to support analysis, recommendations, and reasonable hypotheses.",
    "Check whether the certainty of each claim matches the strength of the evidence, especially when general management possibilities are applied to the specific company.",
    "Do not penalize reasonable synthesis, paraphrasing, hypotheses expressed with appropriate uncertainty, or omission of retrieved information.",
    "Weight faithfulness errors by their importance to the report: unsupported claims that materially affect the core diagnosis, causal explanation, or recommended action should matter more than peripheral unsupported details.",
    "Judge faithfulness as a whole based on evidential support and calibration of certainty, without evaluating relevance or diagnostic quality."
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