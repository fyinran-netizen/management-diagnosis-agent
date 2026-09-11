from __future__ import annotations

from typing import Any

import requests

from app.core.config import OLLAMA_BASE_URL


class OllamaClientError(RuntimeError):
    """Raised when the local Ollama service cannot answer a request."""


def chat_with_ollama(
    messages: list[dict[str, str]],
    model: str,
    temperature: float = 0.2,
    timeout: int = 120,
    num_predict: int = 1200,
    num_ctx: int = 4096,
    think: bool | None = None,
    format: dict[str, Any] | str | None = None,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
        },
    }
    # Keep the production payload unchanged unless a caller opts into one of
    # Ollama's optional request-level controls.
    if think is not None:
        payload["think"] = think
    if format is not None:
        payload["format"] = format

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OllamaClientError(
            f"Failed to connect to Ollama at {OLLAMA_BASE_URL}. "
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
