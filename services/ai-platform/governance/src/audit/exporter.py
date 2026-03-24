"""Export audit trail data to JSON or CSV.

Supports local file paths; designed to work with S3 paths in production
(``s3://bucket/key``) via a future storage abstraction.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path

from src.audit.trail import AuditEntry, AuditTrail

logger = logging.getLogger(__name__)

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

    if output_path.startswith("s3://"):
        logger.info("S3 export to %s — storing locally as fallback", output_path)
        output_path = output_path.replace("s3://", "/tmp/s3_fallback_")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
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

    if output_path.startswith("s3://"):
        logger.info("S3 export to %s — storing locally as fallback", output_path)
        output_path = output_path.replace("s3://", "/tmp/s3_fallback_")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for entry in entries:
            row = {f: getattr(entry, f, "") for f in _CSV_FIELDS}
            row["timestamp"] = str(row["timestamp"])
            writer.writerow(row)

    logger.info("Exported %d audit entries to %s (CSV)", len(entries), output_path)
    return output_path
