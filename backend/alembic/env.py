"""
Alembic Environment — async migration runner.

Reads the database URL from app settings and uses the
async engine for both online and offline migrations.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base

# Import all models here so Base.metadata is populated
import app.models  # noqa: F401

# Alembic Config object
config = context.config

# Setup loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL without DB connection."""
    context.configure(
        url=settings.ASYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Execute migrations against a live connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode — with an async engine."""
    connectable = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entrypoint for online migrations — delegates to async runner."""
    asyncio.run(run_async_migrations())


# ── Execute ─────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
