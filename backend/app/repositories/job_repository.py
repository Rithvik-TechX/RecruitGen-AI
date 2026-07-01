"""
Job Repository — job-specific data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobStatus
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Data access for Job entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Job, session)

    async def get_by_id(self, id: uuid.UUID) -> Job | None:
        """Fetch a single job with its requirements eagerly loaded."""
        stmt = (
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(
        self, *, skip: int = 0, limit: int = 20,
    ) -> list[Job]:
        """Return active jobs across all organizations (candidate view)."""
        stmt = (
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.status == JobStatus.ACTIVE)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_recruiter(
        self,
        recruiter_id: uuid.UUID,
        *,
        status: JobStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Job]:
        """Return jobs owned by a specific recruiter."""
        stmt = (
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.recruiter_id == recruiter_id)
        )
        if status is not None:
            stmt = stmt.where(Job.status == status)
        stmt = stmt.order_by(Job.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        *,
        status: JobStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Job]:
        """Return all jobs in an organization (admin view)."""
        stmt = (
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.organization_id == organization_id)
        )
        if status is not None:
            stmt = stmt.where(Job.status == status)
        stmt = stmt.order_by(Job.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
