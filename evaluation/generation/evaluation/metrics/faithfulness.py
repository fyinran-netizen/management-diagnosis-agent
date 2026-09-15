"""Custom faithfulness metric for management diagnosis generation."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate whether the generated report is faithful to the evidence available in the user input and the retrieval context.",
    "Distinguish among: company-specific facts stated in the user input, general management knowledge provided by the retrieval context, and hypotheses or interpretations introduced by the generated report.",
    "Treat the retrieval context as valid evidence that the report may use for management principles, analytical frameworks, examples, recommendations, and reasonable hypotheses.",
    "Do not assume that a general condition described in the retrieval context is confirmed to exist in the specific company unless the user input or other available evidence establishes that condition.",
    "Allow reasonable hypotheses and diagnostic possibilities when they are clearly expressed with uncertainty appropriate to the available evidence.",
    "Check whether factual, causal, numerical, and company-specific claims are supported by the user input or retrieval context, and whether the strength of each conclusion matches the strength of that evidence.",
    "Pay particular attention to claims that convert a possible explanation into an established company condition, root cause, or causal conclusion without sufficient evidence.",
    "Check unsupported specificity such as numerical values, percentages, thresholds, timelines, operational conditions, or other precise prescriptions when they are introduced as if established by the available evidence.",
    "Before treating a claim, number, example, or causal relationship as unsupported, check whether equivalent supporting information appears anywhere in the retrieval context.",
    "Do not penalize the report for omitting retrieved information, examples, or details; faithfulness evaluates unsupported additions or overstatement, not completeness.",
    "Do not penalize reasonable paraphrasing, synthesis, or general recommendations when their underlying meaning is supported by the available evidence.",
    "Do not judge whether the response is sufficiently relevant, useful, comprehensive, or diagnostically insightful except where those qualities affect evidential support.",
    "A perfect score should require that meaningful factual and causal claims are supported and that uncertainty is calibrated appropriately to the available evidence."
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