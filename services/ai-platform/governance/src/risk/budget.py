"""Token and cost budget management backed by PostgreSQL.

Tracks usage per owner per period, persisted to governance.usage_budget.
The table has a UNIQUE(owner, period, period_start) constraint so
record_usage() uses an upsert to accumulate values atomically.

Falls back to in-memory state when the database is unavailable.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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


_UPSERT_SQL = """
INSERT INTO governance.usage_budget (
    id, owner, period, period_start,
    token_limit, cost_limit_usd, tokens_used, cost_used_usd,
    created_at, updated_at
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now(), now())
ON CONFLICT (owner, period, period_start)
DO UPDATE SET
    tokens_used   = governance.usage_budget.tokens_used   + EXCLUDED.tokens_used,
    cost_used_usd = governance.usage_budget.cost_used_usd + EXCLUDED.cost_used_usd,
    updated_at    = now()
RETURNING id, owner, period, period_start,
          token_limit, cost_limit_usd, tokens_used, cost_used_usd,
          created_at, updated_at
"""

_SELECT_SQL = """
SELECT id, owner, period, period_start,
       token_limit, cost_limit_usd, tokens_used, cost_used_usd,
       created_at, updated_at
FROM governance.usage_budget
WHERE owner = $1 AND period = $2 AND period_start = $3
"""


class BudgetManager:
    """Budget tracker persisted to PostgreSQL with in-memory fallback."""

    def __init__(self) -> None:
        self._budgets: dict[str, Budget] = {}

    def _key(self, owner: str, period: BudgetPeriod) -> str:
        return f"{owner}:{period.value}"

    def get_or_create_budget(
        self,
        owner: str,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
        token_limit: int = 1_000_000,
        cost_limit_usd: float = 100.00,
    ) -> Budget:
        key = self._key(owner, period)
        if key not in self._budgets:
            self._budgets[key] = Budget(
                owner=owner,
                period=period,
                token_limit=token_limit,
                cost_limit_usd=cost_limit_usd,
            )
        return self._budgets[key]

    def check_budget(
        self, owner: str, period: BudgetPeriod = BudgetPeriod.MONTHLY
    ) -> BudgetCheckResult:
        budget = self.get_or_create_budget(owner, period)
        return _compute_result(budget)

    async def check_budget_async(
        self, owner: str, period: BudgetPeriod = BudgetPeriod.MONTHLY
    ) -> BudgetCheckResult:
        """Check budget, reading from DB if available."""
        budget = await self._fetch_from_db(owner, period)
        if budget is None:
            budget = self.get_or_create_budget(owner, period)
        return _compute_result(budget)

    def record_usage(
        self,
        owner: str,
        tokens: int = 0,
        cost_usd: float = 0.0,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
    ) -> Budget:
        """Record usage synchronously (DB write is fire-and-forget)."""
        import asyncio
        budget = self.get_or_create_budget(owner, period)
        budget.tokens_used += tokens
        budget.cost_used_usd += cost_usd
        budget.updated_at = datetime.now(timezone.utc)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._upsert_db(owner, period, tokens, cost_usd, budget))
        except RuntimeError:
            pass
        return budget

    async def record_usage_async(
        self,
        owner: str,
        tokens: int = 0,
        cost_usd: float = 0.0,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
    ) -> Budget:
        """Record usage and await the DB write."""
        budget = self.get_or_create_budget(owner, period)
        budget.tokens_used += tokens
        budget.cost_used_usd += cost_usd
        budget.updated_at = datetime.now(timezone.utc)
        db_budget = await self._upsert_db(owner, period, tokens, cost_usd, budget)
        if db_budget:
            self._budgets[self._key(owner, period)] = db_budget
            return db_budget
        return budget

    # ── DB helpers ────────────────────────────────────────────────────────

    async def _upsert_db(
        self,
        owner: str,
        period: BudgetPeriod,
        tokens: int,
        cost_usd: float,
        budget: Budget,
    ) -> Budget | None:
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            return None
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    _UPSERT_SQL,
                    budget.id, owner, period.value, budget.period_start,
                    budget.token_limit, budget.cost_limit_usd,
                    tokens, cost_usd,
                )
            return _row_to_budget(row) if row else None
        except Exception as exc:
            logger.error("Failed to upsert budget for %s/%s: %s", owner, period.value, exc)
            return None

    async def _fetch_from_db(
        self, owner: str, period: BudgetPeriod
    ) -> Budget | None:
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            return None
        try:
            period_start = date.today()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(_SELECT_SQL, owner, period.value, period_start)
            return _row_to_budget(row) if row else None
        except Exception as exc:
            logger.error("Failed to fetch budget for %s/%s: %s", owner, period.value, exc)
            return None


def _compute_result(budget: Budget) -> BudgetCheckResult:
    token_util = budget.tokens_used / budget.token_limit if budget.token_limit > 0 else 0.0
    cost_util = budget.cost_used_usd / budget.cost_limit_usd if budget.cost_limit_usd > 0 else 0.0
    max_util = max(token_util, cost_util)

    if max_util >= 1.0:
        status = BudgetStatus.EXCEEDED
        message = f"Budget exceeded for {budget.owner} ({budget.period.value})"
    elif max_util >= 0.8:
        status = BudgetStatus.WARNING
        message = f"Budget at {max_util:.0%} for {budget.owner} ({budget.period.value})"
    else:
        status = BudgetStatus.OK
        message = f"Budget OK for {budget.owner} ({budget.period.value})"

    return BudgetCheckResult(
        status=status,
        tokens_remaining=max(budget.token_limit - budget.tokens_used, 0),
        cost_remaining_usd=max(budget.cost_limit_usd - budget.cost_used_usd, 0.0),
        token_utilization=round(token_util, 4),
        cost_utilization=round(cost_util, 4),
        message=message,
    )


def _row_to_budget(row: Any) -> Budget:
    return Budget(
        id=str(row["id"]),
        owner=row["owner"],
        period=BudgetPeriod(row["period"]),
        period_start=row["period_start"],
        token_limit=int(row["token_limit"]),
        cost_limit_usd=float(row["cost_limit_usd"]),
        tokens_used=int(row["tokens_used"]),
        cost_used_usd=float(row["cost_used_usd"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
