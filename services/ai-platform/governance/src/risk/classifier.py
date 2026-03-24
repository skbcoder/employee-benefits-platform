"""Classify a numeric risk score into a discrete risk level.

Uses thresholds from the governance settings.
"""

from __future__ import annotations

from config.settings import get_settings
from src.risk.scorer import RiskLevel


def classify(score: float) -> RiskLevel:
    """Map a 0.0 -- 1.0 score to a :class:`RiskLevel`.

    Thresholds (from settings):
    - critical >= risk_threshold_critical (default 0.9)
    - high     >= risk_threshold_high     (default 0.7)
    - medium   >= 0.3
    - low      <  0.3
    """
    settings = get_settings()

    if score >= settings.risk_threshold_critical:
        return RiskLevel.CRITICAL
    if score >= settings.risk_threshold_high:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
