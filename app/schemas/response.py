from pydantic import BaseModel


class DiagnosisResponse(BaseModel):
    model: str
    diagnosis_report: str