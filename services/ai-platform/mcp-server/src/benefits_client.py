"""HTTP client for the Employee Benefits Platform REST APIs."""

from typing import Any

import httpx

from config.settings import settings


class BenefitsClient:
    """Async HTTP client wrapping enrollment and processing service APIs."""

    def __init__(self) -> None:
        self._enrollment_url = settings.enrollment_service_url.rstrip("/")
        self._processing_url = settings.processing_service_url.rstrip("/")
        self._http: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ── Enrollment Service ──────────────────────────────────────────

    async def submit_enrollment(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = await self._client()
        resp = await client.post(
            f"{self._enrollment_url}/api/enrollments",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_enrollment(self, enrollment_id: str) -> dict[str, Any]:
        client = await self._client()
        resp = await client.get(
            f"{self._enrollment_url}/api/enrollments/{enrollment_id}"
        )
        resp.raise_for_status()
        return resp.json()

    async def get_enrollment_by_employee(self, employee_id: str) -> dict[str, Any]:
        client = await self._client()
        resp = await client.get(
            f"{self._enrollment_url}/api/enrollments/by-employee/{employee_id}"
        )
        resp.raise_for_status()
        return resp.json()

    async def get_enrollment_by_name(self, employee_name: str) -> dict[str, Any]:
        client = await self._client()
        resp = await client.get(
            f"{self._enrollment_url}/api/enrollments/by-name/{employee_name}"
        )
        resp.raise_for_status()
        return resp.json()

    async def list_enrollments_by_status(self, status: str) -> list[dict[str, Any]]:
        client = await self._client()
        resp = await client.get(
            f"{self._enrollment_url}/api/enrollments/by-status",
            params={"status": status},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Processing Service ──────────────────────────────────────────

    async def get_processing_details(self, enrollment_id: str) -> dict[str, Any]:
        client = await self._client()
        resp = await client.get(
            f"{self._processing_url}/api/processed-enrollments/{enrollment_id}"
        )
        resp.raise_for_status()
        return resp.json()

    async def get_processing_by_employee(self, employee_id: str) -> dict[str, Any]:
        client = await self._client()
        resp = await client.get(
            f"{self._processing_url}/api/processed-enrollments/by-employee/{employee_id}"
        )
        resp.raise_for_status()
        return resp.json()

    async def get_processing_by_name(self, employee_name: str) -> dict[str, Any]:
        client = await self._client()
        resp = await client.get(
            f"{self._processing_url}/api/processed-enrollments/by-name/{employee_name}"
        )
        resp.raise_for_status()
        return resp.json()

    # ── Combined ────────────────────────────────────────────────────

    async def check_enrollment_status(self, enrollment_id: str) -> dict[str, Any]:
        """Get enrollment + processing details with effective status."""
        enrollment = await self.get_enrollment(enrollment_id)

        processing = None
        try:
            processing = await self.get_processing_details(enrollment_id)
        except httpx.HTTPStatusError:
            pass  # Processing record may not exist yet

        status_order = {
            "SUBMITTED": 0,
            "DISPATCH_FAILED": 0,
            "PROCESSING": 1,
            "COMPLETED": 2,
        }

        enroll_order = status_order.get(enrollment.get("status", ""), 0)
        proc_order = status_order.get(
            processing.get("status", "") if processing else "", -1
        )

        effective_status = (
            processing["status"] if processing and proc_order > enroll_order
            else enrollment["status"]
        )

        return {
            "enrollmentId": enrollment.get("enrollmentId"),
            "employeeId": enrollment.get("employeeId"),
            "employeeName": enrollment.get("employeeName"),
            "enrollmentStatus": enrollment.get("status"),
            "processingStatus": processing.get("status") if processing else None,
            "effectiveStatus": effective_status,
            "enrollmentUpdatedAt": enrollment.get("updatedAt"),
            "processingUpdatedAt": processing.get("updatedAt") if processing else None,
            "message": enrollment.get("message"),
        }


# Singleton instance
benefits_client = BenefitsClient()
