"""
Job Endpoints — CRUD operations + requirements management.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_or_recruiter, get_current_user
from app.db.session import get_db
from app.models.job import JobStatus
from app.models.user import User
from app.schemas.job import (
    JobCreate,
    JobRequirementCreate,
    JobRequirementResponse,
    JobResponse,
    JobUpdate,
)
from app.services.job_service import JobService

router = APIRouter()


# ── CRUD ────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job posting",
)
async def create_job(
    payload: JobCreate,
    current_user: Annotated[User, Depends(admin_or_recruiter)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobResponse:
    """Create a new job under the caller's organization."""
    service = JobService(session)
    job = await service.create_job(payload, current_user)
    return JobResponse.model_validate(job)


@router.get(
    "/",
    response_model=list[JobResponse],
    summary="List jobs",
)
async def list_jobs(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_filter: JobStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[JobResponse]:
    """List jobs scoped to the caller's role.

    - **Candidate**: all active jobs.
    - **Recruiter**: own jobs (any status).
    - **Admin**: all jobs in their organization.
    """
    service = JobService(session)
    jobs = await service.list_jobs(
        current_user, status_filter=status_filter, skip=skip, limit=limit,
    )
    return [JobResponse.model_validate(j) for j in jobs]


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get a job posting",
)
async def get_job(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobResponse:
    """Retrieve a single job. Candidates may only view active postings."""
    service = JobService(session)
    job = await service.get_job(job_id, current_user)
    return JobResponse.model_validate(job)


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update a job posting",
)
async def update_job(
    job_id: uuid.UUID,
    payload: JobUpdate,
    current_user: Annotated[User, Depends(admin_or_recruiter)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobResponse:
    """Update fields on an existing job (partial update)."""
    service = JobService(session)
    job = await service.update_job(job_id, payload, current_user)
    return JobResponse.model_validate(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job posting",
)
async def delete_job(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_or_recruiter)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a job and all its requirements."""
    service = JobService(session)
    await service.delete_job(job_id, current_user)


# ── Requirements ────────────────────────────────────────────


@router.post(
    "/{job_id}/requirements",
    response_model=list[JobRequirementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add requirements to a job",
)
async def add_requirements(
    job_id: uuid.UUID,
    payloads: list[JobRequirementCreate],
    current_user: Annotated[User, Depends(admin_or_recruiter)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[JobRequirementResponse]:
    """Append one or more skill requirements to a job posting."""
    service = JobService(session)
    reqs = await service.add_requirements(job_id, payloads, current_user)
    return [JobRequirementResponse.model_validate(r) for r in reqs]
