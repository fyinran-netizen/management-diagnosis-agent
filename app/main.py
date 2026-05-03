from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.agent.graph import run_diagnosis_workflow
from app.llm.ollama_client import OllamaClientError, get_ollama_config
from app.schemas.request import DiagnosisRequest
from app.schemas.response import DiagnosisResponse, RetrievedSource, VerificationResult

app = FastAPI(
    title="Management Diagnosis Agent",
    description="A local LangGraph-based management diagnosis agent prototype.",
    version="0.2.0",
)


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


@app.post("/diagnose", response_model=DiagnosisResponse)
def diagnose_management_problem(request: DiagnosisRequest) -> DiagnosisResponse:
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

    return DiagnosisResponse(
        model=model,
        diagnosis_report=result.get("final_answer", result.get("report", "")),
        retrieved_sources=retrieved_sources,
        verification=verification,
        revision_count=result.get("revision_count", 0),
        project_id=result.get("project_id"),
    )