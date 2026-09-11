"""DeepEval adapter backed by the project's existing Ollama client."""

from __future__ import annotations

import asyncio
from typing import Any

from deepeval.models import DeepEvalBaseLLM

from app.core.config import GENERATION_EVALUATION_MODEL
from app.llm.ollama_client import chat_with_ollama


JUDGE_TEMPERATURE = 0.0
JUDGE_NUM_PREDICT = 2048
JUDGE_NUM_CTX = 8192


class OllamaDeepEvalModel(DeepEvalBaseLLM):
    """Use the configured local Ollama model as DeepEval's judge."""

    def __init__(self, model: str = GENERATION_EVALUATION_MODEL) -> None:
        self._model_name = model
        super().__init__(model=model)

    def load_model(self) -> "OllamaDeepEvalModel":
        # The actual client is intentionally shared with generation and the
        # rest of the application; no second HTTP implementation is introduced.
        return self

    @staticmethod
    def _schema_format(schema: Any) -> dict[str, Any] | None:
        if schema is None:
            return None
        if hasattr(schema, "model_json_schema"):
            return schema.model_json_schema()
        if isinstance(schema, dict):
            return schema
        raise TypeError(f"Unsupported DeepEval schema type: {type(schema)!r}")

    def generate(self, prompt: str, schema: Any = None, **_: Any) -> str:
        return chat_with_ollama(
            [{"role": "user", "content": prompt}],
            model=self._model_name,
            temperature=JUDGE_TEMPERATURE,
            num_predict=JUDGE_NUM_PREDICT,
            num_ctx=JUDGE_NUM_CTX,
            # Qwen3 can spend the whole prediction budget in its reasoning
            # channel. The judge needs the final JSON in message.content.
            think=False,
            format=self._schema_format(schema),
        )

    async def a_generate(self, prompt: str, schema: Any = None, **_: Any) -> str:
        return await asyncio.to_thread(self.generate, prompt, schema=schema)

    def get_model_name(self) -> str:
        return self._model_name

    def supports_temperature(self) -> bool:
        return True

    def supports_structured_outputs(self) -> bool:
        return True

    def supports_json_mode(self) -> bool:
        return True
