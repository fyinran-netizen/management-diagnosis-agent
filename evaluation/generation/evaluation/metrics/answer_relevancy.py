"""Custom answer relevancy metric for management diagnosis generation."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate whether the generated report stays focused on the management problem and question described in the user input.",
    "Treat diagnosis, management concepts, root-cause analysis, recommendations, missing information, and explicit assumptions as relevant when they help understand or address the user's problem.",
    "Do not penalize the response merely because it contains analysis before recommendations or because it includes necessary assumptions and missing-information sections.",
    "Check whether the core diagnosis directly addresses the user's stated problem.",
    "Check whether the root-cause discussion is meaningfully connected to the user's problem rather than introducing unrelated management topics.",
    "Check whether the recommendations directly help the company respond to the problem described in the input.",
    "Penalize irrelevant theory, examples, background information, or recommendations that do not materially contribute to answering the user's question.",
    "Penalize excessive tangents or knowledge-base content that is included only because it was retrieved, rather than because it is useful for the current problem.",
    "A perfect score should mean that nearly all substantive parts of the report contribute to diagnosing or addressing the user's actual management problem.",
]


def build_metric(model):
    """Build the custom answer relevancy GEval metric."""
    return GEval(
        name="Answer Relevancy",
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
        ],
        evaluation_steps=EVALUATION_STEPS,
        model=model,
        async_mode=False,
    )