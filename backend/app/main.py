"""
RecruitmentGen AI — FastAPI Application Factory.

This module creates and configures the FastAPI application:
- Lifespan: initialises logging, verifies DB, logs readiness
- CORS middleware
- Health endpoints (/, /health, /health/db)
- v1 API router
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.db.init_db import init_db
from app.db.session import engine, AsyncSessionLocal
from app.api.v1.router import api_v1_router

logger = structlog.get_logger(__name__)


# ── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup & shutdown logic."""
    # Startup
    setup_logging()
    settings = get_settings()
    logger.info(
        "application_starting",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        debug=settings.DEBUG,
    )
    await init_db()
    logger.info("application_ready", docs_url="/docs")

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await engine.dispose()
    logger.info("database_engine_disposed")


# ── Application Factory ────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered recruitment platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS Middleware ─────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health Endpoints ────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint — basic service info."""
        return {
            "service": settings.APP_NAME,
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Application health check."""
        return {
            "status": "healthy",
            "environment": settings.APP_ENV,
        }

    @app.get("/health/db", tags=["Health"])
    async def health_db() -> dict:
        """Database connectivity health check."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()  # consume the result
            return {
                "status": "healthy",
                "database": "connected",
            }
        except Exception as exc:
            logger.error("health_db_check_failed", error=str(exc))
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "detail": str(exc),
            }

    # ── API Routers ─────────────────────────────────────────
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


# ── Module-level app instance (used by uvicorn) ────────────
app = create_app()
