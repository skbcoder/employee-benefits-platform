"""Data retention policy enforcement.

Identifies audit entries that exceed the configured retention period.
Follows the append-only principle: entries are *flagged* for purge but
never deleted by this module.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from config.settings import get_settings
from src.audit.trail import AuditEntry


def check_retention(audit_entries: list[AuditEntry]) -> list[AuditEntry]:
    """Return entries whose timestamp exceeds the retention window.

    These entries *should* be purged according to the retention policy,
    but this function only flags them -- it does not delete anything
    (append-only principle).
    """
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.audit_retention_days)

    return [
        entry for entry in audit_entries
        if entry.timestamp < cutoff
    ]
