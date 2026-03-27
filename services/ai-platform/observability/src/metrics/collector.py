"""Prometheus metrics collector and FastAPI middleware."""

import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ── Metrics ──────────────────────────────────────────────────────────

agent_request_duration_seconds = Histogram(
    "agent_request_duration_seconds",
    "Duration of agent requests in seconds",
    labelnames=["agent", "status"],
)

agent_request_total = Counter(
    "agent_request_total",
    "Total number of agent requests",
    labelnames=["agent", "status"],
)

agent_tool_call_total = Counter(
    "agent_tool_call_total",
    "Total number of tool calls",
    labelnames=["tool_name"],
)

agent_token_usage_total = Counter(
    "agent_token_usage_total",
    "Total token usage across models",
    labelnames=["model"],
)

agent_guardrail_trigger_total = Counter(
    "agent_guardrail_trigger_total",
    "Total guardrail triggers",
    labelnames=["guardrail_type"],
)

agent_governance_decision_total = Counter(
    "agent_governance_decision_total",
    "Total governance decisions",
    labelnames=["decision"],
)

rag_search_duration_seconds = Histogram(
    "rag_search_duration_seconds",
    "Duration of RAG search operations in seconds",
    labelnames=["service"],
)

pii_detection_total = Counter(
    "pii_detection_total",
    "Total PII detections",
    labelnames=["pii_type"],
)

agent_cost_usd = Gauge(
    "agent_cost_usd",
    "Estimated cost in USD",
    labelnames=["model", "period"],
)


# ── Middleware ────────────────────────────────────────────────────────


class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that instruments request duration and count."""

    def __init__(self, app, service_name: str = "unknown"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start

        status = str(response.status_code)
        agent_request_duration_seconds.labels(
            agent=self.service_name, status=status
        ).observe(duration)
        agent_request_total.labels(
            agent=self.service_name, status=status
        ).inc()

        return response


# ── Endpoint ─────────────────────────────────────────────────────────


def metrics_endpoint() -> str:
    """Return Prometheus text format metrics."""
    return generate_latest().decode("utf-8")


# ── Helpers ──────────────────────────────────────────────────────────


def record_tool_call(name: str) -> None:
    agent_tool_call_total.labels(tool_name=name).inc()


def record_token_usage(model: str, tokens: int) -> None:
    agent_token_usage_total.labels(model=model).inc(tokens)


def record_guardrail_trigger(guardrail_type: str) -> None:
    agent_guardrail_trigger_total.labels(guardrail_type=guardrail_type).inc()


def record_governance_decision(decision: str) -> None:
    agent_governance_decision_total.labels(decision=decision).inc()


def record_pii_detection(pii_type: str) -> None:
    pii_detection_total.labels(pii_type=pii_type).inc()


def observe_rag_search(service: str, duration: float) -> None:
    rag_search_duration_seconds.labels(service=service).observe(duration)


def set_cost(model: str, period: str, usd: float) -> None:
    agent_cost_usd.labels(model=model, period=period).set(usd)
