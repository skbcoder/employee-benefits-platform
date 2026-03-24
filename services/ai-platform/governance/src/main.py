"""Governance Service — FastAPI application.

Provides pre-action policy checks, post-response review (PII detection),
approval workflows, audit trail, and compliance reporting.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

# Observability — shared module
_observability_available = False
try:
    _obs_base = Path(__file__).parent.parent.parent / "observability"
    _spec = importlib.util.spec_from_file_location(
        "obs_metrics", _obs_base / "src" / "metrics" / "collector.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    MetricsMiddleware = _mod.MetricsMiddleware
    metrics_endpoint = _mod.metrics_endpoint
    _observability_available = True
except Exception:
    pass

from config.settings import get_settings
from src.approval.queue import ApprovalQueue
from src.approval.workflow import ApprovalStatus, ApprovalWorkflow
from src.audit.exporter import export_csv, export_json
from src.audit.trail import AuditEntry, AuditTrail
from src.compliance.pii_detector import detect_pii, redact_pii, score_pii_risk
from src.compliance.reporter import generate_report
from src.policies.engine import PolicyEngine, PolicyEffect
from src.policies.loader import load_policies_from_directory
from src.risk.scorer import score_action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title="Governance Service",
    description="Policy enforcement, audit trail, risk scoring, PII detection, and compliance reporting.",
    version="0.1.0",
)

# Observability
if _observability_available:
    app.add_middleware(MetricsMiddleware, service_name="governance")

    @app.get("/metrics")
    async def metrics():
        return Response(content=metrics_endpoint(), media_type="text/plain")

# Policy engine
policy_engine = PolicyEngine()
_policy_dir = Path(__file__).resolve().parent.parent / "policies"
if _policy_dir.is_dir():
    policy_engine.add_policies(load_policies_from_directory(_policy_dir))
    logger.info("Loaded %d policies from %s", len(policy_engine.policies), _policy_dir)

# Approval workflow & queue
approval_workflow = ApprovalWorkflow()
approval_queue = ApprovalQueue(approval_workflow)

# Audit trail
audit_trail = AuditTrail()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class GovernanceCheckRequest(BaseModel):
    agent: str
    action: str
    context: dict[str, Any] = Field(default_factory=dict)
    conversation_id: str = ""


class GovernanceCheckResponse(BaseModel):
    allowed: bool
    effects: list[str] = Field(default_factory=list)
    matched_policies: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str = ""
    risk_score: float = 0.0
    risk_level: str = "low"
    risk_factors: list[dict[str, Any]] = Field(default_factory=list)
    approval_id: str | None = None


class ReviewRequest(BaseModel):
    agent: str
    action: str = "respond"
    response_text: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    conversation_id: str = ""


class ReviewResponse(BaseModel):
    allowed: bool
    redacted_text: str = ""
    pii_detected: list[dict[str, Any]] = Field(default_factory=list)
    pii_risk_score: float = 0.0
    policy_decision: dict[str, Any] = Field(default_factory=dict)
    risk_score: float = 0.0
    risk_level: str = "low"


class ApprovalActionRequest(BaseModel):
    reviewer: str
    notes: str = ""


class AuditExportRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    format: str = "json"
    output_path: str = ""


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "governance",
        "policies_loaded": len(policy_engine.policies),
        "audit_entries": len(audit_trail),
    }


# ---------------------------------------------------------------------------
# Pre-action policy check
# ---------------------------------------------------------------------------

@app.post("/api/governance/check", response_model=GovernanceCheckResponse)
async def governance_check(request: GovernanceCheckRequest):
    """Evaluate policies and risk before an agent action is executed."""
    # Policy evaluation.
    decision = policy_engine.evaluate(request.agent, request.action, request.context)

    # Risk scoring.
    risk = score_action(request.agent, request.action, request.context)

    # If approval is required, create an approval request.
    approval_id: str | None = None
    if PolicyEffect.REQUIRE_APPROVAL in decision.effects:
        approval_req = await approval_queue.add(
            conversation_id=request.conversation_id,
            agent=request.agent,
            action=request.action,
            context=request.context,
            risk_level=risk.level.value,
            risk_score=risk.score,
        )
        approval_id = approval_req.id

    # Audit log.
    audit_trail.log_audit(AuditEntry(
        event_type="pre_check",
        conversation_id=request.conversation_id,
        agent=request.agent,
        action=request.action,
        request_summary=f"Check: {request.agent}/{request.action}",
        risk_level=risk.level.value,
        risk_score=risk.score,
        policy_decisions=[decision.model_dump(mode="json")],
    ))

    return GovernanceCheckResponse(
        allowed=decision.allowed,
        effects=[e.value for e in decision.effects],
        matched_policies=[m.model_dump() for m in decision.matched_policies],
        explanation=decision.explanation,
        risk_score=risk.score,
        risk_level=risk.level.value,
        risk_factors=[f.model_dump() for f in risk.factors],
        approval_id=approval_id,
    )


# ---------------------------------------------------------------------------
# Post-response review
# ---------------------------------------------------------------------------

@app.post("/api/governance/review", response_model=ReviewResponse)
async def governance_review(request: ReviewRequest):
    """Review an agent response for PII and policy compliance."""
    # PII detection.
    pii_detections = detect_pii(request.response_text) if settings.pii_detection_enabled else []
    pii_risk = score_pii_risk(pii_detections)
    redacted = redact_pii(request.response_text) if pii_detections else request.response_text

    # Build context for policy check.
    ctx = {**request.context, "response": request.response_text}
    decision = policy_engine.evaluate(request.agent, request.action, ctx)

    # Risk scoring with PII info.
    risk_ctx = {
        **request.context,
        "pii_present": len(pii_detections) > 0,
        "pii_count": len(pii_detections),
    }
    risk = score_action(request.agent, request.action, risk_ctx)

    # If redact effect is present, use redacted text.
    final_text = redacted if PolicyEffect.REDACT in decision.effects or pii_detections else request.response_text

    # Audit log.
    audit_trail.log_audit(AuditEntry(
        event_type="post_review",
        conversation_id=request.conversation_id,
        agent=request.agent,
        action=request.action,
        request_summary=f"Review: {request.agent}/{request.action}",
        response_summary=final_text[:500],
        risk_level=risk.level.value,
        risk_score=risk.score,
        policy_decisions=[decision.model_dump(mode="json")],
        pii_detected=[d.model_dump() for d in pii_detections],
    ))

    return ReviewResponse(
        allowed=decision.allowed,
        redacted_text=final_text,
        pii_detected=[d.model_dump() for d in pii_detections],
        pii_risk_score=pii_risk,
        policy_decision=decision.model_dump(mode="json"),
        risk_score=risk.score,
        risk_level=risk.level.value,
    )


# ---------------------------------------------------------------------------
# Approval endpoints
# ---------------------------------------------------------------------------

@app.get("/api/governance/approvals")
async def list_approvals():
    """List all pending approval requests."""
    pending = await approval_queue.get_pending()
    return {"approvals": [r.model_dump(mode="json") for r in pending]}


@app.post("/api/governance/approvals/{approval_id}/approve")
async def approve_request(approval_id: str, body: ApprovalActionRequest):
    result = await approval_queue.update_status(
        approval_id, ApprovalStatus.APPROVED, body.reviewer, body.notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="Approval request not found or not pending")

    audit_trail.log_audit(AuditEntry(
        event_type="approval_approved",
        agent=result.agent,
        action=result.action,
        conversation_id=result.conversation_id,
        metadata={"reviewer": body.reviewer, "notes": body.notes},
    ))

    return result.model_dump(mode="json")


@app.post("/api/governance/approvals/{approval_id}/deny")
async def deny_request(approval_id: str, body: ApprovalActionRequest):
    result = await approval_queue.update_status(
        approval_id, ApprovalStatus.DENIED, body.reviewer, body.notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="Approval request not found or not pending")

    audit_trail.log_audit(AuditEntry(
        event_type="approval_denied",
        agent=result.agent,
        action=result.action,
        conversation_id=result.conversation_id,
        metadata={"reviewer": body.reviewer, "notes": body.notes},
    ))

    return result.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Audit endpoints
# ---------------------------------------------------------------------------

@app.get("/api/governance/audit")
async def query_audit(
    event_type: str | None = Query(None),
    conversation_id: str | None = Query(None),
    agent: str | None = Query(None),
    risk_level: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Query the audit trail with optional filters."""
    entries = audit_trail.query_audit(
        event_type=event_type,
        conversation_id=conversation_id,
        agent=agent,
        risk_level=risk_level,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return {"entries": [e.model_dump(mode="json") for e in entries], "count": len(entries)}


@app.post("/api/governance/audit/export")
async def export_audit(request: AuditExportRequest):
    """Trigger an audit data export to JSON or CSV."""
    output = request.output_path or f"audit_export.{request.format}"

    if request.format == "csv":
        path = export_csv(audit_trail, request.start_date, request.end_date, output)
    else:
        path = export_json(audit_trail, request.start_date, request.end_date, output)

    return {"status": "exported", "path": path, "format": request.format}


# ---------------------------------------------------------------------------
# Compliance report
# ---------------------------------------------------------------------------

@app.get("/api/governance/compliance/report")
async def compliance_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
):
    """Generate a compliance report for the given date range."""
    report = generate_report(audit_trail, start_date, end_date)
    return report.model_dump(mode="json")
