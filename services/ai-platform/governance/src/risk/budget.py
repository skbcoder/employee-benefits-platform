"""Token and cost budget management.

Tracks usage per owner (user or team) per period.  In-memory for now;
designed for PostgreSQL backing via the ``governance.usage_budget`` table.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class BudgetPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class BudgetStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    EXCEEDED = "exceeded"


class Budget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    owner: str
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    period_start: date = Field(default_factory=lambda: date.today())
    token_limit: int = 1_000_000
    cost_limit_usd: float = 100.00
    tokens_used: int = 0
    cost_used_usd: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BudgetCheckResult(BaseModel):
    status: BudgetStatus
    tokens_remaining: int
    cost_remaining_usd: float
    token_utilization: float
    cost_utilization: float
    message: str = ""


class BudgetManager:
    """In-memory budget tracker."""

    def __init__(self) -> None:
        self._budgets: dict[str, Budget] = {}

    def get_or_create_budget(
        self,
        owner: str,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
        token_limit: int = 1_000_000,
        cost_limit_usd: float = 100.00,
    ) -> Budget:
        key = f"{owner}:{period.value}"
        if key not in self._budgets:
            self._budgets[key] = Budget(
                owner=owner,
                period=period,
                token_limit=token_limit,
                cost_limit_usd=cost_limit_usd,
            )
        return self._budgets[key]

    def check_budget(self, owner: str, period: BudgetPeriod = BudgetPeriod.MONTHLY) -> BudgetCheckResult:
        budget = self.get_or_create_budget(owner, period)

        token_util = budget.tokens_used / budget.token_limit if budget.token_limit > 0 else 0.0
        cost_util = budget.cost_used_usd / budget.cost_limit_usd if budget.cost_limit_usd > 0 else 0.0
        max_util = max(token_util, cost_util)

        if max_util >= 1.0:
            status = BudgetStatus.EXCEEDED
            message = f"Budget exceeded for {owner} ({budget.period.value})"
        elif max_util >= 0.8:
            status = BudgetStatus.WARNING
            message = f"Budget at {max_util:.0%} for {owner} ({budget.period.value})"
        else:
            status = BudgetStatus.OK
            message = f"Budget OK for {owner} ({budget.period.value})"

        return BudgetCheckResult(
            status=status,
            tokens_remaining=max(budget.token_limit - budget.tokens_used, 0),
            cost_remaining_usd=max(budget.cost_limit_usd - budget.cost_used_usd, 0.0),
            token_utilization=round(token_util, 4),
            cost_utilization=round(cost_util, 4),
            message=message,
        )

    def record_usage(
        self,
        owner: str,
        tokens: int = 0,
        cost_usd: float = 0.0,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
    ) -> Budget:
        budget = self.get_or_create_budget(owner, period)
        budget.tokens_used += tokens
        budget.cost_used_usd += cost_usd
        budget.updated_at = datetime.now(timezone.utc)
        return budget
