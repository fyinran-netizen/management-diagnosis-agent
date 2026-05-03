from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    company_context: str = Field(
        ...,
        min_length=10,
        description="Description of the company's current situation or management challenge.",
    )
    goal: str | None = Field(
        default="Please provide a management diagnosis and practical recommendations.",
        description="The user's analysis goal.",
    )
    language: str = Field(
        default="zh",
        description="Output language. Use 'zh' for Chinese or 'en' for English.",
    )