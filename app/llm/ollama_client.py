from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv


class OllamaClientError(RuntimeError):
    pass


load_dotenv()


def get_ollama_config() -> tuple[str, str]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen3")
    return base_url, model


def chat_with_ollama(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.2,
    timeout: int = 120,
) -> str:
    base_url, default_model = get_ollama_config()
    selected_model = model or default_model

    payload: dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 1200,
            "num_ctx": 4096,
        },
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OllamaClientError(
            f"Failed to connect to Ollama at {base_url}. "
            f"Make sure Ollama is running."
        ) from exc

    if response.status_code != 200:
        raise OllamaClientError(
            f"Ollama returned status {response.status_code}: {response.text}"
        )

    data = response.json()
    content = data.get("message", {}).get("content")

    if not content:
        raise OllamaClientError(f"Ollama response did not contain message content: {data}")

    return content.strip()