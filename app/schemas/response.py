from pydantic import BaseModel


class RetrievedSource(BaseModel):
    source: str
    title: str
    content: str
    score: int


class VerificationResult(BaseModel):
    passed: bool
    issues: list[str]
    needs_revision: bool


class DiagnosisResponse(BaseModel):
    model: str
    diagnosis_report: str
    retrieved_sources: list[RetrievedSource]
    verification: VerificationResult
    revision_count: int
    project_id: str | None = None