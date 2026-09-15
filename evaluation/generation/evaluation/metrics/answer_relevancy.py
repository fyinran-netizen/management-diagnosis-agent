"""Custom answer relevancy metric for management diagnosis generation."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Evaluate whether the generated report directly addresses the management question, problem, or decision described in the user input.",
    "Identify the major parts of the user's request and check whether each important part is substantively addressed rather than only mentioned.",
    "Treat diagnosis, management concepts, root-cause analysis, recommendations, missing information, and assumptions as relevant only when they materially help answer the user's actual request.",
    "Check whether the core diagnosis or main conclusion responds to the central issue raised by the user.",
    "Check whether supporting analysis remains connected to the user's problem and contributes to understanding, deciding, or acting on that problem.",
    "Check whether recommendations, when included, address the problem the user actually raised rather than adjacent management issues.",
    "Penalize substantial content that is only topically related but does not materially contribute to answering the user's request.",
    "Penalize unnecessary expansion into diagnosis, theory, background, or recommendations when that expansion adds little value to the question being asked.",
    "Do not judge whether claims are factually supported or whether causal reasoning is correct; those belong to Faithfulness and Diagnosis Quality.",
    "A perfect score should require both strong coverage of the user's important requests and strong focus, with nearly all substantive content contributing to the answer."
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