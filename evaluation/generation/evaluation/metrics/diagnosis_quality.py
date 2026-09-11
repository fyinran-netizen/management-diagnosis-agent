"""Diagnosis quality metric configuration."""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams


EVALUATION_STEPS = [
    "Check whether the core management diagnosis is explicit, clear, and directly addresses the company problem described in the input.",
    "Distinguish carefully between three types of information: facts explicitly stated in the user input, general management knowledge from the retrieval context, and hypotheses inferred by the generated report.",
    "Penalize the report if it presents an inferred hypothesis as a confirmed fact about the company when the input does not provide enough evidence.",
    "Check whether the root-cause analysis is reasonable, distinguishes root causes from surface symptoms, and avoids causal conclusions stronger than the available evidence supports.",
    "Check whether recommendations are logically consistent with the diagnosis and are supported by either the input or the retrieval context.",
    "Penalize invented or unsupported details, including numerical thresholds, percentages, company conditions, causal relationships, or operational facts that are not supported by the input or retrieval context.",
    "Check whether recommendations are specific, practical, and executable for the company, without mechanically copying examples from the retrieval context that may not fit the company's actual situation.",
    "A response should not receive a perfect score if it contains meaningful unsupported assumptions, overconfident causal claims, or recommendations based on evidence that has not been established for this company.",
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
