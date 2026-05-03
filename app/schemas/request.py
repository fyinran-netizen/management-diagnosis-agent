from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        description=(
            "The user's raw description of the company's situation, problem, "
            "and expected analysis goal. It can be informal or unstructured."
        ),
    )