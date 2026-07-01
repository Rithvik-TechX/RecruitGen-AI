"""
Application Endpoints — apply, list, status management.

Exposes two routers:
  • ``router``                  → mounted at ``/applications``
  • ``job_applications_router`` → mounted at ``/jobs`` (for the nested path)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr, candidate_only, get_current_user
from app.db.session import get_db
from app.models.application import ApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)
from app.services.application_service import ApplicationService

router = APIRouter()
job_applications_router = APIRouter()


def _serialize(app) -> ApplicationResponse:
    """Convert ORM Application to response, populating relationship fields."""
    resp = ApplicationResponse.model_validate(app)
    if hasattr(app, "candidate") and app.candidate:
        resp.candidate_name = app.candidate.full_name
    if hasattr(app, "job") and app.job:
        resp.job_title = app.job.title
    return resp


# ── Candidate endpoints (mounted at /applications) ─────────


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for a job",
)
async def apply_for_job(
    payload: ApplicationCreate,
    current_user: Annotated[User, Depends(candidate_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationResponse:
    """Submit an application. Only candidates may apply."""
    service = ApplicationService(session)
    application = await service.apply(payload, current_user)
    return _serialize(application)


@router.get(
    "/me",
    response_model=list[ApplicationResponse],
    summary="My applications",
)
async def get_my_applications(
    current_user: Annotated[User, Depends(candidate_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ApplicationResponse]:
    """List all applications submitted by the current candidate."""
    service = ApplicationService(session)
    apps = await service.list_my_applications(
        current_user, status_filter=status_filter, skip=skip, limit=limit,
    )
    return [_serialize(a) for a in apps]


@router.get(
    "/",
    response_model=list[ApplicationResponse],
    summary="List all applications (admin / recruiter)",
)
async def list_all_applications(
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[ApplicationResponse]:
    """List all applications visible to the current recruiter/admin."""
    service = ApplicationService(session)
    apps = await service.list_all_applications(
        current_user, status_filter=status_filter, skip=skip, limit=limit,
    )
    return [
        ApplicationResponse.model_validate(item)
        for item in await service.enrich_applications(apps)
    ]


@router.get(
    "/pipeline",
    response_model=list[ApplicationResponse],
    summary="List candidates in the HR pipeline",
)
async def list_pipeline_candidates(
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    job_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
) -> list[ApplicationResponse]:
    service = ApplicationService(session)
    applications = await service.list_pipeline(
        current_user,
        job_id=job_id,
        skip=skip,
        limit=limit,
    )
    return [
        ApplicationResponse.model_validate(item)
        for item in await service.enrich_applications(applications)
    ]


# ── Recruiter / Admin endpoints (mounted at /applications) ──


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update application status",
)
async def update_application_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationResponse:
    """Advance an application through the hiring pipeline."""
    service = ApplicationService(session)
    application = await service.update_status(
        application_id, payload, current_user,
    )
    return _serialize(application)


# ── Nested under /jobs (separate router) ────────────────────


@job_applications_router.get(
    "/{job_id}/applications",
    response_model=list[ApplicationResponse],
    summary="List applications for a job",
    tags=["Applications"],
)
async def get_job_applications(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ApplicationResponse]:
    """List all applications for a job posting (recruiter / admin only)."""
    service = ApplicationService(session)
    apps = await service.list_job_applications(
        job_id, current_user,
        status_filter=status_filter, skip=skip, limit=limit,
    )
    return [
        ApplicationResponse.model_validate(item)
        for item in await service.enrich_applications(apps)
    ]
