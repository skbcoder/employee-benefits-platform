"""Token budget enforcement — prevents runaway LLM costs per request."""

from __future__ import annotations

import logging

from config.settings import settings
from src.models.state import TokenUsage

logger = logging.getLogger(__name__)


class TokenBudgetExceeded(Exception):
    """Raised when a request exceeds its token budget."""

    def __init__(self, used: int, budget: int) -> None:
        self.used = used
        self.budget = budget
        super().__init__(f"Token budget exceeded: {used}/{budget}")


def check_budget(usage: TokenUsage) -> None:
    """Check if token usage is within budget. Raises TokenBudgetExceeded if not."""
    budget = settings.token_budget_max
    warn_threshold = int(budget * settings.token_budget_warn_pct)

    if usage.total_tokens >= budget:
        raise TokenBudgetExceeded(usage.total_tokens, budget)

    if usage.total_tokens >= warn_threshold:
        logger.warning(
            f"Token budget warning: {usage.total_tokens}/{budget} "
            f"({usage.total_tokens / budget:.0%}) — approaching limit"
        )
