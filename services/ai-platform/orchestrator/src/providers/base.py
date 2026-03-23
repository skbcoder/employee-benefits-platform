"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models.state import TokenUsage


class LLMResponse(ABC):
    """Normalized response from any LLM provider."""

    @property
    @abstractmethod
    def content(self) -> str:
        """The text content of the response."""

    @property
    @abstractmethod
    def tool_calls(self) -> list[dict[str, Any]]:
        """Tool calls requested by the model, if any."""

    @property
    @abstractmethod
    def usage(self) -> TokenUsage:
        """Token usage for this response."""


class LLMProvider(ABC):
    """Abstract interface for LLM providers (Ollama, Bedrock, etc.)."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send a chat completion request."""

    @abstractmethod
    async def classify(
        self,
        prompt: str,
        model: str | None = None,
    ) -> str:
        """Simple classification — returns the model's text response.

        Used for routing where we only need a short structured answer,
        not a full conversation.
        """
