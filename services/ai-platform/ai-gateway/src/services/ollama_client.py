"""Ollama SDK wrapper for chat completions."""

import json
import logging
from typing import Any

import ollama

from config.settings import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Wraps Ollama Python SDK for chat completions with tool support."""

    def __init__(self) -> None:
        self._client = ollama.AsyncClient(host=settings.ollama_base_url)
        self._model = settings.ollama_chat_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request to Ollama.

        Returns the full response dict including message and any tool_calls.
        """
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self._client.chat(**kwargs)
        return response

    async def is_healthy(self) -> bool:
        """Check if Ollama is reachable and the model is available."""
        try:
            response = await self._client.list()
            model_names = [m.model for m in response.models]
            return any(self._model in name for name in model_names)
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False


ollama_client = OllamaClient()
