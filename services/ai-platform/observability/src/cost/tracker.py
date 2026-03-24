"""Cost tracking for LLM usage."""

import asyncio
from collections import defaultdict
from datetime import date

BEDROCK_PRICING = {
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.001, "output": 0.005},
    "us.anthropic.claude-sonnet-4-20250514-v1:0": {"input": 0.003, "output": 0.015},
    "llama3.1:8b": {"input": 0.0, "output": 0.0},  # Local Ollama
}


class CostTracker:
    """Thread-safe LLM cost tracker with daily summaries."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._daily_totals: dict[str, dict] = defaultdict(
            lambda: {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
        )
        self._by_model: dict[str, dict[str, dict]] = defaultdict(
            lambda: defaultdict(
                lambda: {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
            )
        )

    @staticmethod
    def get_request_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for a single request."""
        pricing = BEDROCK_PRICING.get(model)
        if pricing is None:
            return 0.0
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def record(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Record token usage and return the cost."""
        cost = self.get_request_cost(model, prompt_tokens, completion_tokens)
        today = date.today().isoformat()

        async with self._lock:
            self._daily_totals[today]["prompt_tokens"] += prompt_tokens
            self._daily_totals[today]["completion_tokens"] += completion_tokens
            self._daily_totals[today]["cost_usd"] += cost

            self._by_model[today][model]["prompt_tokens"] += prompt_tokens
            self._by_model[today][model]["completion_tokens"] += completion_tokens
            self._by_model[today][model]["cost_usd"] += cost

        return cost

    async def get_daily_summary(self) -> dict:
        """Get today's cost summary."""
        today = date.today().isoformat()

        async with self._lock:
            totals = dict(self._daily_totals.get(today, {
                "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0,
            }))
            by_model = {
                model: dict(data)
                for model, data in self._by_model.get(today, {}).items()
            }

        total_tokens = totals["prompt_tokens"] + totals["completion_tokens"]
        return {
            "date": today,
            "total_tokens": total_tokens,
            "total_cost_usd": round(totals["cost_usd"], 6),
            "by_model": by_model,
        }
