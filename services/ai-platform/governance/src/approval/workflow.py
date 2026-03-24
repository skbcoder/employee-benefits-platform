"""Human-in-the-loop approval workflow.

Manages the lifecycle of approval requests: creation, review (approve /
deny), and expiry detection.  State is kept in-memory with the design
ready for PostgreSQL backing via the approval_request table.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from config.settings import get_settings


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


class ApprovalWorkflow:
    """Manages approval requests backed by an in-memory store."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
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
        """Create a new pending approval request."""
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
        return request

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        """Return all requests currently in *pending* status."""
        self._expire_stale()
        return [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]

    def get_by_id(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def approve(self, request_id: str, reviewer: str, notes: str = "") -> ApprovalRequest | None:
        """Mark a request as approved."""
        req = self._requests.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return None
        req.status = ApprovalStatus.APPROVED
        req.reviewer = reviewer
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_notes = notes
        return req

    def deny(self, request_id: str, reviewer: str, notes: str = "") -> ApprovalRequest | None:
        """Mark a request as denied."""
        req = self._requests.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return None
        req.status = ApprovalStatus.DENIED
        req.reviewer = reviewer
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_notes = notes
        return req

    def check_expired(self) -> list[ApprovalRequest]:
        """Return requests that just transitioned to expired."""
        return self._expire_stale()

    def _expire_stale(self) -> list[ApprovalRequest]:
        now = datetime.now(timezone.utc)
        expired: list[ApprovalRequest] = []
        for req in self._requests.values():
            if req.status == ApprovalStatus.PENDING and req.expires_at and req.expires_at <= now:
                req.status = ApprovalStatus.EXPIRED
                expired.append(req)
        return expired
