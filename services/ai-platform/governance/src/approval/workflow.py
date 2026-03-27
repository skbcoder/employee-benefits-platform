"""Human-in-the-loop approval workflow backed by PostgreSQL.

Persists approval requests to governance.approval_request.
Falls back to in-memory state when the database is unavailable so the
service continues to operate in degraded mode.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from config.settings import get_settings  # noqa: E402
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str = ""
    agent: str = ""
    action: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "low"
    risk_score: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None


_INSERT_SQL = """
INSERT INTO governance.approval_request (
    id, conversation_id, agent, action, context,
    risk_level, risk_score, status, created_at, expires_at
) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10)
"""

_UPDATE_SQL = """
UPDATE governance.approval_request
SET status = $2, reviewer = $3, reviewed_at = $4, review_notes = $5
WHERE id = $1 AND status = 'pending'
RETURNING id, conversation_id, agent, action, context,
          risk_level, risk_score, status, created_at, expires_at,
          reviewer, reviewed_at, review_notes
"""

_EXPIRE_SQL = """
UPDATE governance.approval_request
SET status = 'expired'
WHERE status = 'pending' AND expires_at <= now()
RETURNING id
"""

_SELECT_PENDING_SQL = """
SELECT id, conversation_id, agent, action, context,
       risk_level, risk_score, status, created_at, expires_at,
       reviewer, reviewed_at, review_notes
FROM governance.approval_request
WHERE status = 'pending' AND expires_at > now()
ORDER BY created_at DESC
"""

_SELECT_BY_ID_SQL = """
SELECT id, conversation_id, agent, action, context,
       risk_level, risk_score, status, created_at, expires_at,
       reviewer, reviewed_at, review_notes
FROM governance.approval_request
WHERE id = $1
"""


class ApprovalWorkflow:
    """Manages approval requests persisted to PostgreSQL."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}  # in-memory fallback
        self._settings = get_settings()

    def create_approval(
        self,
        conversation_id: str,
        agent: str,
        action: str,
        context: dict[str, Any] | None = None,
        risk_level: str = "medium",
        risk_score: float = 0.0,
    ) -> ApprovalRequest:
        """Create a pending approval request (sync — DB write is fire-and-forget)."""
        import asyncio
        now = datetime.now(timezone.utc)
        request = ApprovalRequest(
            conversation_id=conversation_id,
            agent=agent,
            action=action,
            context=context or {},
            risk_level=risk_level,
            risk_score=risk_score,
            created_at=now,
            expires_at=now + timedelta(minutes=self._settings.approval_timeout_minutes),
        )
        self._requests[request.id] = request
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._insert_db(request))
        except RuntimeError:
            pass  # No running event loop — degraded mode
        return request

    async def create_approval_async(
        self,
        conversation_id: str,
        agent: str,
        action: str,
        context: dict[str, Any] | None = None,
        risk_level: str = "medium",
        risk_score: float = 0.0,
    ) -> ApprovalRequest:
        """Create a pending approval request and await the DB write."""
        now = datetime.now(timezone.utc)
        request = ApprovalRequest(
            conversation_id=conversation_id,
            agent=agent,
            action=action,
            context=context or {},
            risk_level=risk_level,
            risk_score=risk_score,
            created_at=now,
            expires_at=now + timedelta(minutes=self._settings.approval_timeout_minutes),
        )
        self._requests[request.id] = request
        await self._insert_db(request)
        return request

    async def get_pending_approvals_async(self) -> list[ApprovalRequest]:
        """Return pending approvals from DB, falling back to in-memory."""
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            return self.get_pending_approvals()
        try:
            async with pool.acquire() as conn:
                await conn.execute(_EXPIRE_SQL)
                rows = await conn.fetch(_SELECT_PENDING_SQL)
            return [_row_to_request(r) for r in rows]
        except Exception as exc:
            logger.error("Failed to fetch pending approvals from DB: %s", exc)
            return self.get_pending_approvals()

    async def get_by_id_async(self, request_id: str) -> ApprovalRequest | None:
        """Fetch a single approval request from DB."""
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            return self.get_by_id(request_id)
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(_SELECT_BY_ID_SQL, request_id)
            if row is None:
                return None
            req = _row_to_request(row)
            self._requests[req.id] = req  # sync cache
            return req
        except Exception as exc:
            logger.error("Failed to fetch approval %s from DB: %s", request_id, exc)
            return self.get_by_id(request_id)

    async def update_status_async(
        self,
        request_id: str,
        status: ApprovalStatus,
        reviewer: str = "",
        notes: str = "",
    ) -> ApprovalRequest | None:
        """Update approval status in DB and return the updated request."""
        from src.db import get_pool
        pool = await get_pool()
        now = datetime.now(timezone.utc)

        if pool is None:
            if status == ApprovalStatus.APPROVED:
                return self.approve(request_id, reviewer, notes)
            elif status == ApprovalStatus.DENIED:
                return self.deny(request_id, reviewer, notes)
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    _UPDATE_SQL, request_id, status.value, reviewer or None, now, notes or None
                )
            if row is None:
                return None
            req = _row_to_request(row)
            self._requests[req.id] = req
            return req
        except Exception as exc:
            logger.error("Failed to update approval %s in DB: %s", request_id, exc)
            if status == ApprovalStatus.APPROVED:
                return self.approve(request_id, reviewer, notes)
            elif status == ApprovalStatus.DENIED:
                return self.deny(request_id, reviewer, notes)
            return None

    # ── In-memory fallback methods (unchanged interface) ──────────────────

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        self._expire_stale()
        return [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]

    def get_by_id(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def approve(self, request_id: str, reviewer: str, notes: str = "") -> ApprovalRequest | None:
        req = self._requests.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return None
        req.status = ApprovalStatus.APPROVED
        req.reviewer = reviewer
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_notes = notes
        return req

    def deny(self, request_id: str, reviewer: str, notes: str = "") -> ApprovalRequest | None:
        req = self._requests.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return None
        req.status = ApprovalStatus.DENIED
        req.reviewer = reviewer
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_notes = notes
        return req

    def check_expired(self) -> list[ApprovalRequest]:
        return self._expire_stale()

    def _expire_stale(self) -> list[ApprovalRequest]:
        now = datetime.now(timezone.utc)
        expired: list[ApprovalRequest] = []
        for req in self._requests.values():
            if req.status == ApprovalStatus.PENDING and req.expires_at and req.expires_at <= now:
                req.status = ApprovalStatus.EXPIRED
                expired.append(req)
        return expired

    # ── DB helpers ────────────────────────────────────────────────────────

    async def _insert_db(self, request: ApprovalRequest) -> None:
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            return
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    _INSERT_SQL,
                    request.id,
                    request.conversation_id,
                    request.agent,
                    request.action,
                    json.dumps(request.context),
                    request.risk_level,
                    request.risk_score,
                    request.status.value,
                    request.created_at,
                    request.expires_at,
                )
        except Exception as exc:
            logger.error("Failed to persist approval request %s: %s", request.id, exc)


def _row_to_request(row: Any) -> ApprovalRequest:
    return ApprovalRequest(
        id=str(row["id"]),
        conversation_id=row["conversation_id"] or "",
        agent=row["agent"] or "",
        action=row["action"] or "",
        context=row["context"] or {},
        risk_level=row["risk_level"] or "low",
        risk_score=float(row["risk_score"] or 0.0),
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        status=ApprovalStatus(row["status"]),
        reviewer=row["reviewer"],
        reviewed_at=row["reviewed_at"],
        review_notes=row["review_notes"],
    )
