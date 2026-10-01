from __future__ import annotations

from contextvars import ContextVar
from time import perf_counter
from typing import Any

import requests

from app.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT,
    OLLAMA_TEMPERATURE,
    OLLAMA_TIMEOUT,
)
from app.core.logging import get_logger


class OllamaClientError(RuntimeError):
    """Raised when the local Ollama service cannot answer a request."""


logger = get_logger("ollama")
_last_call_metrics: ContextVar[dict[str, Any]] = ContextVar(
    "last_ollama_call_metrics",
    default={},
)


def get_last_call_metrics() -> dict[str, Any]:
    return dict(_last_call_metrics.get())


def chat_with_ollama(
    messages: list[dict[str, str]],
    model: str,
    temperature: float | None = None,
    timeout: int | None = None,
    num_predict: int | None = None,
    num_ctx: int | None = None,
    think: bool | None = None,
    format: dict[str, Any] | str | None = None,
) -> str:
    started_at = perf_counter()
    temperature = OLLAMA_TEMPERATURE if temperature is None else temperature
    timeout = OLLAMA_TIMEOUT if timeout is None else timeout
    num_predict = OLLAMA_NUM_PREDICT if num_predict is None else num_predict
    num_ctx = OLLAMA_NUM_CTX if num_ctx is None else num_ctx

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

    logger.debug(
        "ollama request model=%s message_count=%d prompt_chars=%d roles=%s",
        model,
        len(messages),
        sum(len(message.get("content", "")) for message in messages),
        [message.get("role") for message in messages],
    )

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
    metrics = {
        "elapsed_seconds": perf_counter() - started_at,
        "eval_count": data.get("eval_count"),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "done_reason": data.get("done_reason"),
    }
    _last_call_metrics.set(metrics)
    logger.info(
        "ollama completed model=%s elapsed_seconds=%.3f eval_count=%s "
        "prompt_eval_count=%s done_reason=%s",
        model,
        metrics["elapsed_seconds"],
        metrics["eval_count"],
        metrics["prompt_eval_count"],
        metrics["done_reason"],
    )
    content = data.get("message", {}).get("content")

    if not content:
        raise OllamaClientError(f"Ollama response did not contain message content: {data}")

    return content.strip()
