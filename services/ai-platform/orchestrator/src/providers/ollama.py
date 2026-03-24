"""Ollama LLM provider for local development."""

from __future__ import annotations

import logging
from typing import Any

import ollama as ollama_lib

from config.settings import settings
from src.models.state import TokenUsage
from src.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaResponse(LLMResponse):
    """Wraps an Ollama chat response into the normalized interface."""

    def __init__(self, raw: Any) -> None:
        self._raw = raw
        self._message = (
            raw.message if hasattr(raw, "message") else raw.get("message", {})
        )

    @property
    def content(self) -> str:
        if hasattr(self._message, "content"):
            return self._message.content or ""
        return self._message.get("content", "")

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        calls = (
            self._message.tool_calls
            if hasattr(self._message, "tool_calls")
            else self._message.get("tool_calls")
        )
        if not calls:
            return []
        result = []
        for tc in calls:
            fn = tc.function if hasattr(tc, "function") else tc.get("function", {})
            name = fn.name if hasattr(fn, "name") else fn.get("name", "")
            args = fn.arguments if hasattr(fn, "arguments") else fn.get("arguments", {})
            result.append({"name": name, "arguments": args})
        return result

    @property
    def usage(self) -> TokenUsage:
        # Ollama provides eval_count and prompt_eval_count
        prompt = getattr(self._raw, "prompt_eval_count", 0) or 0
        completion = getattr(self._raw, "eval_count", 0) or 0
        return TokenUsage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
            model=getattr(self._raw, "model", ""),
        )


class OllamaProvider(LLMProvider):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self) -> None:
        self._client = ollama_lib.AsyncClient(host=settings.ollama_base_url)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> OllamaResponse:
        model = model or settings.ollama_agent_model
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        if max_tokens:
            kwargs["options"] = {"num_predict": max_tokens}

        response = await self._client.chat(**kwargs)
        return OllamaResponse(response)

    async def classify(
        self,
        prompt: str,
        model: str | None = None,
    ) -> str:
        model = model or settings.ollama_router_model
        response = await self._client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 256, "temperature": 0.1},
        )
        return OllamaResponse(response).content
