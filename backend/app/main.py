"""
RecruitmentGen AI — FastAPI Application Factory.
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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

    logger.info("application_shutting_down")
    await engine.dispose()
    logger.info("database_engine_disposed")


def create_app() -> FastAPI:
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
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "https://YOUR-AMPLIFY-URL.amplifyapp.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )



    @app.get("/", tags=["Root"])
    async def root() -> dict:
        return {
            "service": settings.APP_NAME,
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "environment": settings.APP_ENV,
        }

    @app.get("/health/db", tags=["Health"])
    async def health_db() -> dict:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()

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

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()