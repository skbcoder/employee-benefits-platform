"""Database connection pool for the governance service.

Uses asyncpg directly — no ORM needed for simple INSERT/SELECT operations
against the governance schema.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import asyncpg

from config.settings import get_settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    """Create the connection pool and ensure the governance schema exists."""
    global _pool
    settings = get_settings()
    dsn = (
        f"postgresql://{quote_plus(settings.db_username)}:{quote_plus(settings.db_password)}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    try:
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
        # Run migration if tables don't exist yet
        async with _pool.acquire() as conn:
            await _apply_migration(conn)
        logger.info("Governance database pool initialised.")
    except Exception as exc:
        logger.error("Failed to connect to database: %s — running in degraded mode.", exc)
        _pool = None


async def close_db() -> None:
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool | None:
    """Return the active pool, or None if DB is unavailable."""
    return _pool


async def _apply_migration(conn: asyncpg.Connection) -> None:
    """Idempotently create governance schema and tables if they don't exist."""
    from pathlib import Path
    migration = Path(__file__).parent.parent / "migrations" / "V1__create_governance_schema.sql"
    if not migration.exists():
        logger.warning("Migration file not found at %s — skipping schema creation.", migration)
        return
    sql = migration.read_text()
    try:
        await conn.execute(sql)
    except asyncpg.exceptions.DuplicateObjectError:
        pass  # Already applied — triggers / indexes already exist
    except Exception as exc:
        # Individual statement failures (e.g. table already exists) are expected
        # on subsequent starts; log at warning level for visibility.
        logger.warning("Migration note (likely already applied): %s", exc)
