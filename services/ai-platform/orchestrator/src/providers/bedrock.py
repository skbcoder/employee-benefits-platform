"""AWS Bedrock LLM provider for production deployments."""

from __future__ import annotations

import json
import logging
from typing import Any

from config.settings import settings
from src.models.state import TokenUsage
from src.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Bedrock pricing per 1K tokens (approximate, us-east-1)
_BEDROCK_PRICING: dict[str, dict[str, float]] = {
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.001, "output": 0.005},
    "us.anthropic.claude-sonnet-4-20250514-v1:0": {"input": 0.003, "output": 0.015},
}


class BedrockResponse(LLMResponse):
    """Wraps a Bedrock Converse API response."""

    def __init__(self, raw: dict[str, Any], model_id: str) -> None:
        self._raw = raw
        self._model_id = model_id

    @property
    def content(self) -> str:
        output = self._raw.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        texts = [b["text"] for b in content_blocks if "text" in b]
        return "\n".join(texts)

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        output = self._raw.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        calls = []
        for block in content_blocks:
            if "toolUse" in block:
                tu = block["toolUse"]
                calls.append({
                    "name": tu.get("name", ""),
                    "arguments": tu.get("input", {}),
                    "toolUseId": tu.get("toolUseId", ""),
                })
        return calls

    @property
    def usage(self) -> TokenUsage:
        usage = self._raw.get("usage", {})
        prompt = usage.get("inputTokens", 0)
        completion = usage.get("outputTokens", 0)
        pricing = _BEDROCK_PRICING.get(self._model_id, {})
        cost = (
            (prompt / 1000) * pricing.get("input", 0)
            + (completion / 1000) * pricing.get("output", 0)
        )
        return TokenUsage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
            model=self._model_id,
            estimated_cost_usd=round(cost, 6),
        )


class BedrockProvider(LLMProvider):
    """LLM provider backed by AWS Bedrock Converse API."""

    def __init__(self) -> None:
        try:
            import boto3

            self._client = boto3.client(
                "bedrock-runtime", region_name=settings.bedrock_region
            )
        except Exception:
            logger.warning("Bedrock client init failed — AWS credentials may be missing")
            self._client = None

    def _to_converse_messages(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Convert standard message format to Bedrock Converse format.

        Returns (converse_messages, system_prompt).
        """
        system_prompt = None
        converse_msgs = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role in ("user", "assistant"):
                converse_msgs.append({
                    "role": role,
                    "content": [{"text": content}],
                })
            elif role == "tool":
                converse_msgs.append({
                    "role": "user",
                    "content": [{"toolResult": {"toolUseId": "tool", "content": [{"text": content}]}}],
                })

        return converse_msgs, system_prompt

    def _to_converse_tools(
        self, tools: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert MCP tool definitions to Bedrock Converse tool format."""
        converse_tools = []
        for tool in tools:
            fn = tool.get("function", tool)
            converse_tools.append({
                "toolSpec": {
                    "name": fn.get("name", ""),
                    "description": fn.get("description", ""),
                    "inputSchema": {
                        "json": fn.get("parameters", fn.get("inputSchema", {}))
                    },
                }
            })
        return converse_tools

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> BedrockResponse:
        if not self._client:
            raise RuntimeError("Bedrock client not initialized — check AWS credentials")

        model_id = model or settings.bedrock_agent_model_id
        converse_msgs, system_prompt = self._to_converse_messages(messages)

        kwargs: dict[str, Any] = {
            "modelId": model_id,
            "messages": converse_msgs,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": max_tokens or 4096,
            },
        }

        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]

        if tools:
            kwargs["toolConfig"] = {"tools": self._to_converse_tools(tools)}

        # Bedrock Converse is synchronous — run in executor for async compat
        import asyncio

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self._client.converse(**kwargs)
        )
        return BedrockResponse(response, model_id)

    async def classify(
        self,
        prompt: str,
        model: str | None = None,
    ) -> str:
        model_id = model or settings.bedrock_router_model_id
        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.1,
            max_tokens=256,
        )
        return response.content
