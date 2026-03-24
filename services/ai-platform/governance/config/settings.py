"""Governance service configuration via Pydantic settings."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class GovernanceSettings(BaseSettings):
    """Configuration for the governance service.

    Values are loaded from environment variables (case-insensitive) with
    the defaults shown below.
    """

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    # Database
    db_host: str = "localhost"
    db_port: int = int(os.environ.get("DB_PORT", "5433"))
    db_name: str = "employee_benefits_platform"
    db_username: str = "benefits_app"
    db_password: str = "benefits_app"

    # Service
    governance_port: int = 8500
    governance_host: str = "0.0.0.0"

    # Approval workflow
    approval_timeout_minutes: int = 30

    # Audit
    audit_retention_days: int = 365

    # Risk thresholds
    risk_threshold_high: float = 0.7
    risk_threshold_critical: float = 0.9

    # Compliance
    pii_detection_enabled: bool = True

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection string for SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchronous PostgreSQL connection string."""
        return (
            f"postgresql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )



def get_settings() -> GovernanceSettings:
    """Return a cached settings instance."""
    return GovernanceSettings()
