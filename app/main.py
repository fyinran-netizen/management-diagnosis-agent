from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.llm.ollama_client import OllamaClientError, chat_with_ollama, get_ollama_config
from app.schemas.request import DiagnosisRequest
from app.schemas.response import DiagnosisResponse

app = FastAPI(
    title="Management Diagnosis Agent",
    description="A local LLM-powered management diagnosis agent prototype.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnosisResponse)
def diagnose_management_problem(request: DiagnosisRequest) -> DiagnosisResponse:
    _, model = get_ollama_config()

    output_language = "Chinese" if request.language == "zh" else "English"

    messages = [
        {
            "role": "system",
            "content": (
                "You are a management diagnosis assistant for enterprise managers. "
                "Your task is to analyze company management challenges and provide structured, practical advice. "
                "Do not invent company facts. If information is missing, clearly state the assumptions. "
                "Use a calm, professional consulting style."
                "Do not use hidden reasoning. Give the final answer directly."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Output language: {output_language}\n\n"
                f"Company context:\n{request.company_context}\n\n"
                f"Analysis goal:\n{request.goal}\n\n"
                "Please provide a structured management diagnosis with the following sections:\n"
                "1. Core diagnosis\n"
                "2. Possible root causes\n"
                "3. Management perspective\n"
                "4. Practical recommendations\n"
                "5. Missing information and assumptions\n"
            ),
        },
    ]

    try:
        diagnosis_report = chat_with_ollama(messages)
    except OllamaClientError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DiagnosisResponse(
        model=model,
        diagnosis_report=diagnosis_report,
    )