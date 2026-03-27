"""Compliance report generation.

Builds summary reports from in-memory audit data.  Designed for future
DB-backed aggregation queries.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.audit.trail import AuditTrail


class ComplianceReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    total_blocked: int = 0
    policy_violations: int = 0
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    pii_detections: int = 0
    approval_stats: dict[str, int] = Field(default_factory=dict)
    audit_summary: dict[str, Any] = Field(default_factory=dict)


def generate_report(
    trail: AuditTrail,
    start_date: datetime,
    end_date: datetime,
) -> ComplianceReport:
    """Generate a compliance report for the given date range."""
    entries = trail.query_audit(start_date=start_date, end_date=end_date, limit=999_999)

    risk_counts: Counter[str] = Counter()
    blocked = 0
    violations = 0
    pii_total = 0
    event_type_counts: Counter[str] = Counter()
    agent_counts: Counter[str] = Counter()

    for entry in entries:
        risk_counts[entry.risk_level] += 1
        event_type_counts[entry.event_type] += 1
        if entry.agent:
            agent_counts[entry.agent] += 1

        # Count PII detections.
        if entry.pii_detected:
            pii_total += len(entry.pii_detected)

        # Count blocked / violated decisions.
        for decision in entry.policy_decisions:
            if isinstance(decision, dict):
                if not decision.get("allowed", True):
                    blocked += 1
                effects = decision.get("effects", [])
                if "deny" in effects:
                    violations += 1

    return ComplianceReport(
        period_start=start_date,
        period_end=end_date,
        total_requests=len(entries),
        total_blocked=blocked,
        policy_violations=violations,
        risk_distribution=dict(risk_counts),
        pii_detections=pii_total,
        approval_stats={},  # Populated when approval workflow is DB-backed.
        audit_summary={
            "event_types": dict(event_type_counts),
            "agents": dict(agent_counts),
            "entry_count": len(entries),
        },
    )
