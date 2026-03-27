"""Thread-safe in-memory approval queue backed by the workflow store.

Provides an async-safe interface over :class:`ApprovalWorkflow` using an
``asyncio.Lock`` to prevent concurrent state mutations.
"""

from __future__ import annotations

import asyncio
from typing import Any

from src.approval.workflow import ApprovalRequest, ApprovalStatus, ApprovalWorkflow


class ApprovalQueue:
    """Async-safe wrapper around the approval workflow."""

    def __init__(self, workflow: ApprovalWorkflow | None = None) -> None:
        self._workflow = workflow or ApprovalWorkflow()
        self._lock = asyncio.Lock()

    async def add(
        self,
        conversation_id: str,
        agent: str,
        action: str,
        context: dict[str, Any] | None = None,
        risk_level: str = "medium",
        risk_score: float = 0.0,
    ) -> ApprovalRequest:
        async with self._lock:
            return await self._workflow.create_approval_async(
                conversation_id=conversation_id,
                agent=agent,
                action=action,
                context=context,
                risk_level=risk_level,
                risk_score=risk_score,
            )

    async def get_pending(self) -> list[ApprovalRequest]:
        async with self._lock:
            return await self._workflow.get_pending_approvals_async()

    async def get_by_id(self, request_id: str) -> ApprovalRequest | None:
        async with self._lock:
            return await self._workflow.get_by_id_async(request_id)

    async def update_status(
        self,
        request_id: str,
        status: ApprovalStatus,
        reviewer: str = "",
        notes: str = "",
    ) -> ApprovalRequest | None:
        async with self._lock:
            if status == ApprovalStatus.APPROVED:
                return self._workflow.approve(request_id, reviewer, notes)
            elif status == ApprovalStatus.DENIED:
                return self._workflow.deny(request_id, reviewer, notes)
            return None

    async def update_status_db(
        self,
        request_id: str,
        status: ApprovalStatus,
        reviewer: str = "",
        notes: str = "",
    ) -> ApprovalRequest | None:
        async with self._lock:
            return await self._workflow.update_status_async(request_id, status, reviewer, notes)
