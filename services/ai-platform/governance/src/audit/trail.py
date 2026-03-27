"""Immutable audit trail backed by PostgreSQL.

Writes go directly to governance.audit_trail via asyncpg INSERT.
The table has BEFORE UPDATE / BEFORE DELETE triggers that raise exceptions,
enforcing append-only semantics at the database level.

Queries fall back to an in-memory cache when the database is unavailable
so the service continues to operate in degraded mode.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    conversation_id: str = ""
    agent: str = ""
    action: str = ""
    request_summary: str = ""
    response_summary: str = ""
    risk_level: str = "low"
    risk_score: float = 0.0
    policy_decisions: list[dict[str, Any]] = Field(default_factory=list)
    pii_detected: list[dict[str, Any]] = Field(default_factory=list)
    client_ip: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


_INSERT_SQL = """
INSERT INTO governance.audit_trail (
    id, timestamp, event_type, conversation_id, agent, action,
    request_summary, response_summary, risk_level, risk_score,
    policy_decisions, pii_detected, client_ip, metadata
) VALUES (
    $1, $2, $3, $4, $5, $6,
    $7, $8, $9, $10,
    $11::jsonb, $12::jsonb, $13, $14::jsonb
)
"""

_SELECT_SQL = """
SELECT id, timestamp, event_type, conversation_id, agent, action,
       request_summary, response_summary, risk_level, risk_score,
       policy_decisions, pii_detected, client_ip, metadata
FROM governance.audit_trail
WHERE ($1::text IS NULL OR event_type = $1)
  AND ($2::text IS NULL OR conversation_id = $2)
  AND ($3::text IS NULL OR agent = $3)
  AND ($4::text IS NULL OR risk_level = $4)
  AND ($5::timestamptz IS NULL OR timestamp >= $5)
  AND ($6::timestamptz IS NULL OR timestamp <= $6)
ORDER BY timestamp DESC
LIMIT $7
"""


class AuditTrail:
    """Append-only audit trail.

    Writes to PostgreSQL; maintains a bounded in-memory cache as a
    fallback for queries when the database is temporarily unavailable.
    """

    _CACHE_LIMIT = 500  # keep at most this many entries in memory

    def __init__(self) -> None:
        self._cache: list[AuditEntry] = []

    def log_audit(self, entry: AuditEntry) -> AuditEntry:
        """Persist an entry. Fires-and-forgets the DB write; always succeeds."""
        import asyncio
        # Keep in-memory cache (bounded)
        self._cache.append(entry)
        if len(self._cache) > self._CACHE_LIMIT:
            self._cache = self._cache[-self._CACHE_LIMIT:]

        # Schedule async DB write without blocking the caller
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._write_to_db(entry))
        except RuntimeError:
            pass  # No running event loop — degraded mode (e.g. tests)

        return entry

    async def log_audit_async(self, entry: AuditEntry) -> AuditEntry:
        """Persist an entry and await the DB write (use from async contexts)."""
        self._cache.append(entry)
        if len(self._cache) > self._CACHE_LIMIT:
            self._cache = self._cache[-self._CACHE_LIMIT:]
        await self._write_to_db(entry)
        return entry

    async def _write_to_db(self, entry: AuditEntry) -> None:
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            return
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    _INSERT_SQL,
                    entry.id,
                    entry.timestamp,
                    entry.event_type,
                    entry.conversation_id or None,
                    entry.agent or None,
                    entry.action or None,
                    entry.request_summary or None,
                    entry.response_summary or None,
                    entry.risk_level,
                    entry.risk_score,
                    json.dumps(entry.policy_decisions),
                    json.dumps(entry.pii_detected),
                    entry.client_ip or None,
                    json.dumps(entry.metadata),
                )
        except Exception as exc:
            logger.error("Failed to persist audit entry %s: %s", entry.id, exc)

    async def query_audit_db(
        self,
        *,
        event_type: str | None = None,
        conversation_id: str | None = None,
        agent: str | None = None,
        risk_level: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit entries from PostgreSQL."""
        from src.db import get_pool
        pool = await get_pool()
        if pool is None:
            logger.warning("DB unavailable — returning in-memory audit cache.")
            return self.query_audit(
                event_type=event_type,
                conversation_id=conversation_id,
                agent=agent,
                risk_level=risk_level,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    _SELECT_SQL,
                    event_type, conversation_id, agent, risk_level,
                    start_date, end_date, limit,
                )
            return [_row_to_entry(r) for r in rows]
        except Exception as exc:
            logger.error("Audit DB query failed: %s — falling back to cache.", exc)
            return self.query_audit(
                event_type=event_type,
                conversation_id=conversation_id,
                agent=agent,
                risk_level=risk_level,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

    def query_audit(
        self,
        *,
        event_type: str | None = None,
        conversation_id: str | None = None,
        agent: str | None = None,
        risk_level: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query in-memory cache (fallback when DB is unavailable)."""
        results: list[AuditEntry] = []
        for entry in reversed(self._cache):
            if event_type and entry.event_type != event_type:
                continue
            if conversation_id and entry.conversation_id != conversation_id:
                continue
            if agent and entry.agent != agent:
                continue
            if risk_level and entry.risk_level != risk_level:
                continue
            if start_date and entry.timestamp < start_date:
                continue
            if end_date and entry.timestamp > end_date:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    @property
    def entries(self) -> list[AuditEntry]:
        """Read-only view of the in-memory cache."""
        return list(self._cache)

    def __len__(self) -> int:
        return len(self._cache)


def _row_to_entry(row: Any) -> AuditEntry:
    return AuditEntry(
        id=str(row["id"]),
        timestamp=row["timestamp"],
        event_type=row["event_type"] or "",
        conversation_id=row["conversation_id"] or "",
        agent=row["agent"] or "",
        action=row["action"] or "",
        request_summary=row["request_summary"] or "",
        response_summary=row["response_summary"] or "",
        risk_level=row["risk_level"] or "low",
        risk_score=float(row["risk_score"] or 0.0),
        policy_decisions=row["policy_decisions"] or [],
        pii_detected=row["pii_detected"] or [],
        client_ip=row["client_ip"] or "",
        metadata=row["metadata"] or {},
    )
