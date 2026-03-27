"""Export audit trail data to JSON or CSV.

Supports local file paths; designed to work with S3 paths in production
(``s3://bucket/key``) via a future storage abstraction.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

from src.audit.trail import AuditEntry, AuditTrail

logger = logging.getLogger(__name__)

# Safe export directory — all exports are written here, never arbitrary paths.
_EXPORT_DIR = Path("/tmp/governance_exports")


def _safe_output_path(requested: str, extension: str) -> str:
    """Return a safe output path within the export directory.

    Prevents path traversal by ignoring the requested path structure
    and generating a filename within the controlled export directory.
    """
    _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    # Strip any directory components — only use the filename
    safe_name = Path(requested).name
    if not safe_name or safe_name.startswith("."):
        safe_name = f"audit_export.{extension}"
    # Ensure correct extension
    if not safe_name.endswith(f".{extension}"):
        safe_name = f"{safe_name}.{extension}"
    return str(_EXPORT_DIR / safe_name)


# Fields included in CSV exports.
_CSV_FIELDS = [
    "id",
    "timestamp",
    "event_type",
    "conversation_id",
    "agent",
    "action",
    "request_summary",
    "response_summary",
    "risk_level",
    "risk_score",
    "client_ip",
]


def _filter_entries(
    trail: AuditTrail,
    start_date: datetime | None,
    end_date: datetime | None,
) -> list[AuditEntry]:
    return trail.query_audit(start_date=start_date, end_date=end_date, limit=999_999)


def export_json(
    trail: AuditTrail,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    output_path: str = "audit_export.json",
) -> str:
    """Export audit entries to a JSON file.

    Returns the output path written to.  If *output_path* starts with
    ``s3://`` a placeholder message is logged (actual S3 upload is a
    future enhancement).
    """
    entries = _filter_entries(trail, start_date, end_date)
    payload = [e.model_dump(mode="json") for e in entries]
    output_path = _safe_output_path(output_path, "json")

    with open(output_path, "w") as fh:
        json.dump(payload, fh, indent=2, default=str)

    logger.info("Exported %d audit entries to %s (JSON)", len(entries), output_path)
    return output_path


def export_csv(
    trail: AuditTrail,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    output_path: str = "audit_export.csv",
) -> str:
    """Export audit entries to a CSV file.

    Returns the output path written to.
    """
    entries = _filter_entries(trail, start_date, end_date)
    output_path = _safe_output_path(output_path, "csv")

    with open(output_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for entry in entries:
            row = {f: getattr(entry, f, "") for f in _CSV_FIELDS}
            row["timestamp"] = str(row["timestamp"])
            writer.writerow(row)

    logger.info("Exported %d audit entries to %s (CSV)", len(entries), output_path)
    return output_path
