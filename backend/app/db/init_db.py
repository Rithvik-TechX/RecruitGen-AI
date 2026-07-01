"""
Database Initialization — startup connectivity check.

Called during the FastAPI lifespan to verify the database is reachable
before accepting traffic.
"""

from __future__ import annotations

import structlog
from sqlalchemy import text

from app.db.session import engine

logger = structlog.get_logger(__name__)


async def verify_db_connection() -> bool:
    """Execute a simple query to verify database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_connection_verified")
        return True
    except Exception as exc:
        logger.error("database_connection_failed", error=str(exc))
        return False


async def init_db() -> None:
    """Initialise the database — run on application startup."""
    connected = await verify_db_connection()
    if not connected:
        logger.warning("database_unavailable_at_startup")
