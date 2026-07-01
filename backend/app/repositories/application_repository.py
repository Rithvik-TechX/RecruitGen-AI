"""
Application Repository — application-specific data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    """Data access for Application entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Application, session)

    async def get_by_id(self, id: uuid.UUID) -> Application | None:
        """Fetch an application with job and candidate eagerly loaded."""
        stmt = (
            select(Application)
            .options(
                selectinload(Application.job),
                selectinload(Application.candidate),
            )
            .where(Application.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> bool:
        """Check whether a candidate has already applied to a job."""
        stmt = select(Application.id).where(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_by_candidate(
        self,
        candidate_id: uuid.UUID,
        *,
        status: ApplicationStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Application]:
        """Return applications submitted by a candidate."""
        stmt = (
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.candidate_id == candidate_id)
        )
        if status is not None:
            stmt = stmt.where(Application.status == status)
        stmt = stmt.order_by(Application.applied_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_job(
        self,
        job_id: uuid.UUID,
        *,
        status: ApplicationStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Application]:
        """Return applications for a specific job posting."""
        stmt = (
            select(Application)
            .options(selectinload(Application.candidate))
            .where(Application.job_id == job_id)
        )
        if status is not None:
            stmt = stmt.where(Application.status == status)
        stmt = stmt.order_by(Application.applied_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        organization_id: uuid.UUID | None = None,
        recruiter_id: uuid.UUID | None = None,
        status: ApplicationStatus | None = None,
        statuses: tuple[ApplicationStatus, ...] | None = None,
        job_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Application]:
        """Return all applications, optionally filtered by org or recruiter."""
        from app.models.job import Job

        stmt = (
            select(Application)
            .join(Job, Application.job_id == Job.id)
            .options(
                selectinload(Application.job),
                selectinload(Application.candidate),
            )
        )
        if organization_id is not None:
            stmt = stmt.where(Job.organization_id == organization_id)
        if recruiter_id is not None:
            stmt = stmt.where(Job.recruiter_id == recruiter_id)
        if status is not None:
            stmt = stmt.where(Application.status == status)
        if statuses:
            stmt = stmt.where(Application.status.in_(statuses))
        if job_id is not None:
            stmt = stmt.where(Application.job_id == job_id)
        stmt = stmt.order_by(Application.applied_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
