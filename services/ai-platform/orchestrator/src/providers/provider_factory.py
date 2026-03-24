"""Factory for creating LLM providers based on configuration."""

from __future__ import annotations

import logging

from config.settings import settings
from src.providers.base import LLMProvider

logger = logging.getLogger(__name__)

_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """Get the configured LLM provider (singleton)."""
    global _provider
    if _provider is not None:
        return _provider

    if settings.llm_provider == "bedrock":
        from src.providers.bedrock import BedrockProvider

        logger.info("Using AWS Bedrock LLM provider")
        _provider = BedrockProvider()
    else:
        from src.providers.ollama import OllamaProvider

        logger.info("Using Ollama LLM provider (local)")
        _provider = OllamaProvider()

    return _provider
