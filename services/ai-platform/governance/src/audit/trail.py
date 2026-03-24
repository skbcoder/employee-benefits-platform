"""Immutable audit trail.

Stores audit entries in an append-only list (in-memory) that mirrors the
``governance.audit_trail`` PostgreSQL table.  The application layer
enforces immutability: entries can be appended and queried but never
modified or deleted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


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


class AuditTrail:
    """Append-only audit trail backed by an in-memory list.

    Designed for future migration to PostgreSQL (write via INSERT only,
    with triggers preventing UPDATE / DELETE on the table).
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def log_audit(self, entry: AuditEntry) -> AuditEntry:
        """Append an entry to the trail. Returns the stored entry."""
        if not entry.id:
            entry.id = str(uuid4())
        if not entry.timestamp:
            entry.timestamp = datetime.now(timezone.utc)
        self._entries.append(entry)
        return entry

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
        """Query the trail with optional filters."""
        results: list[AuditEntry] = []
        for entry in reversed(self._entries):  # newest first
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
        """Read-only view of all entries."""
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
