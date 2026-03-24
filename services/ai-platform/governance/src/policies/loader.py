"""Load policy rules from YAML files on disk.

Scans a directory for ``*.yaml`` / ``*.yml`` files, parses them, and
returns validated :class:`PolicyRule` instances ready for the engine.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from src.policies.engine import (
    ConditionOperator,
    PolicyCondition,
    PolicyEffect,
    PolicyRule,
)

logger = logging.getLogger(__name__)


def _parse_condition(raw: dict) -> PolicyCondition:
    return PolicyCondition(
        field=raw["field"],
        operator=ConditionOperator(raw["operator"]),
        value=raw.get("value"),
    )


def _parse_policy(raw: dict) -> PolicyRule:
    trigger = raw.get("trigger", {})
    conditions = [_parse_condition(c) for c in raw.get("conditions", [])]

    return PolicyRule(
        id=raw["id"],
        description=raw.get("description", ""),
        trigger_agent=trigger.get("agent", "*"),
        trigger_action=trigger.get("action", "*"),
        conditions=conditions,
        effect=PolicyEffect(raw.get("effect", "log")),
        priority=raw.get("priority", 0),
        enabled=raw.get("enabled", True),
    )


def load_policies_from_file(path: Path) -> list[PolicyRule]:
    """Parse a single YAML policy file and return a list of rules."""
    with open(path, "r") as fh:
        data = yaml.safe_load(fh)

    if not data or "policies" not in data:
        logger.warning("No policies found in %s", path)
        return []

    rules: list[PolicyRule] = []
    for entry in data["policies"]:
        try:
            rules.append(_parse_policy(entry))
        except Exception:
            logger.exception("Failed to parse policy in %s: %s", path, entry.get("id", "unknown"))

    return rules


def load_policies_from_directory(directory: str | Path) -> list[PolicyRule]:
    """Scan *directory* for YAML files and return all parsed policies."""
    directory = Path(directory)
    if not directory.is_dir():
        logger.error("Policy directory does not exist: %s", directory)
        return []

    policies: list[PolicyRule] = []
    for pattern in ("*.yaml", "*.yml"):
        for path in sorted(directory.glob(pattern)):
            loaded = load_policies_from_file(path)
            logger.info("Loaded %d policies from %s", len(loaded), path.name)
            policies.extend(loaded)

    return policies
