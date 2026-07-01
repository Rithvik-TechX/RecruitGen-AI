"""
Job Service — job-related business logic and authorization.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobRequirement, JobStatus
from app.models.user import User, UserRole
from app.repositories.job_repository import JobRepository
from app.repositories.job_requirement_repository import JobRequirementRepository
from app.schemas.job import JobCreate, JobRequirementCreate, JobUpdate

logger = structlog.get_logger(__name__)


class JobService:
    """Orchestrates job CRUD, requirements, and role-based authorization."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._job_repo = JobRepository(session)
        self._req_repo = JobRequirementRepository(session)

    # ── authorization helpers ───────────────────────────────

    @staticmethod
    def _ensure_can_manage(job: Job | None, user: User) -> Job:
        """Verify the user has permission to modify this job.

        Rules:
            • Admin  → any job in their own organization.
            • Recruiter → only jobs they created.
            • Candidate → never.

        Raises:
            HTTPException 404: job not found.
            HTTPException 403: insufficient permissions.
        """
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
        if (
            user.role == UserRole.ADMIN
            and job.organization_id == user.organization_id
        ):
            return job
        if (
            user.role == UserRole.RECRUITER
            and job.recruiter_id == user.id
        ):
            return job
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this job.",
        )

    # ── CRUD ────────────────────────────────────────────────

    async def create_job(self, payload: JobCreate, recruiter: User) -> Job:
        """Create a new job posting under the recruiter's organization."""
        job = Job(
            organization_id=recruiter.organization_id,
            recruiter_id=recruiter.id,
            title=payload.title,
            department=payload.department,
            location=payload.location,
            employment_type=payload.employment_type,
            experience_required=payload.experience_required,
            salary_min=payload.salary_min,
            salary_max=payload.salary_max,
            description=payload.description,
            status=payload.status,
        )
        job = await self._job_repo.create(job)
        await self._session.commit()
        await self._session.refresh(job)

        logger.info(
            "job_created",
            job_id=str(job.id),
            title=job.title,
            recruiter_id=str(recruiter.id),
        )
        return job

    async def list_jobs(
        self,
        user: User,
        *,
        status_filter: JobStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Job]:
        """Return jobs scoped to the caller's role.

        • Candidate    → all **active** jobs (cross-org).
        • Recruiter    → own jobs (any status, filterable).
        • HR_MANAGER   → all jobs in their organization (filterable).
        • Admin        → all jobs in their organization (filterable).
        """
        if user.role == UserRole.CANDIDATE:
            return await self._job_repo.list_active(skip=skip, limit=limit)
        if user.role == UserRole.RECRUITER:
            return await self._job_repo.list_by_recruiter(
                user.id, status=status_filter, skip=skip, limit=limit,
            )
        # ADMIN and HR_MANAGER — all jobs in their organization
        return await self._job_repo.list_by_organization(
            user.organization_id,
            status=status_filter,
            skip=skip,
            limit=limit,
        )

    async def get_job(self, job_id: uuid.UUID, user: User) -> Job:
        """Retrieve a single job.

        Candidates may only view active postings.
        """
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
        if user.role == UserRole.CANDIDATE and job.status != JobStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This job is not currently available.",
            )
        return job

    async def update_job(
        self,
        job_id: uuid.UUID,
        payload: JobUpdate,
        user: User,
    ) -> Job:
        """Partially update a job posting."""
        job = await self._job_repo.get_by_id(job_id)
        job = self._ensure_can_manage(job, user)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(job)

        logger.info(
            "job_updated",
            job_id=str(job.id),
            updated_fields=list(update_data.keys()),
        )
        return job

    async def delete_job(self, job_id: uuid.UUID, user: User) -> None:
        """Delete a job and its cascade-deleted requirements."""
        job = await self._job_repo.get_by_id(job_id)
        job = self._ensure_can_manage(job, user)

        await self._job_repo.delete(job)
        await self._session.commit()

        logger.info("job_deleted", job_id=str(job_id))

    # ── Requirements ────────────────────────────────────────

    async def add_requirements(
        self,
        job_id: uuid.UUID,
        payloads: list[JobRequirementCreate],
        user: User,
    ) -> list[JobRequirement]:
        """Append skill requirements to a job posting."""
        job = await self._job_repo.get_by_id(job_id)
        job = self._ensure_can_manage(job, user)

        requirements = [
            JobRequirement(
                job_id=job.id,
                skill_name=p.skill_name,
                importance_weight=p.importance_weight,
                required_level=p.required_level,
            )
            for p in payloads
        ]
        created = await self._req_repo.bulk_create(requirements)
        await self._session.commit()

        logger.info(
            "job_requirements_added",
            job_id=str(job_id),
            count=len(created),
        )
        return created
