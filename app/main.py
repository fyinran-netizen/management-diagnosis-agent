from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.agent.graph import run_diagnosis_workflow
from app.llm.ollama_client import OllamaClientError, get_ollama_config
from app.schemas.request import DiagnosisRequest
from app.schemas.response import (
    DiagnosisDebugResponse,
    DiagnosisResponse,
    PublicRetrievedSource,
    RetrievedSource,
    VerificationResult,
)

app = FastAPI(
    title="Management Diagnosis Agent",
    description="A local LangGraph-based management diagnosis agent prototype.",
    version="0.2.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": app.title,
        "status": "ok",
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/ollama")
def debug_ollama() -> dict[str, str]:
    base_url, model = get_ollama_config()
    return {
        "base_url": base_url,
        "model": model,
    }


def build_diagnosis_result(
    request: DiagnosisRequest,
) -> tuple[DiagnosisResponse, DiagnosisDebugResponse]:
    _, model = get_ollama_config()

    try:
        result = run_diagnosis_workflow(
            description=request.description,
        )
    except OllamaClientError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    retrieved_sources = [
        RetrievedSource(**item)
        for item in result.get("retrieved_chunks", [])
    ]
    public_retrieved_sources = [
        PublicRetrievedSource(
            source=item.source,
            title=item.title,
            score=item.score,
        )
        for item in retrieved_sources
    ]

    verification = VerificationResult(
        **result.get(
            "verification",
            {
                "passed": False,
                "issues": ["Verification result is missing."],
                "needs_revision": True,
            },
        )
    )

    public_response = DiagnosisResponse(
        model=model,
        diagnosis_report=result.get("final_answer", result.get("report", "")),
        retrieved_sources=public_retrieved_sources,
        verification=verification,
        revision_count=result.get("revision_count", 0),
        project_id=result.get("project_id"),
    )
    debug_response = DiagnosisDebugResponse(
        model=model,
        diagnosis_report=result.get("final_answer", result.get("report", "")),
        retrieved_sources=retrieved_sources,
        verification=verification,
        revision_count=result.get("revision_count", 0),
        project_id=result.get("project_id"),
    )
    return public_response, debug_response


@app.post("/diagnose", response_model=DiagnosisResponse)
def diagnose_management_problem(request: DiagnosisRequest) -> DiagnosisResponse:
    public_response, _ = build_diagnosis_result(request)
    return public_response


@app.post("/admin/diagnose", response_model=DiagnosisDebugResponse)
def diagnose_management_problem_admin(request: DiagnosisRequest) -> DiagnosisDebugResponse:
    _, debug_response = build_diagnosis_result(request)
    return debug_response
