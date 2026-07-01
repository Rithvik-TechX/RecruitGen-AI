"""
JobRequirement Repository — requirement-specific data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import JobRequirement
from app.repositories.base import BaseRepository


class JobRequirementRepository(BaseRepository[JobRequirement]):
    """Data access for JobRequirement entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(JobRequirement, session)

    async def list_by_job(self, job_id: uuid.UUID) -> list[JobRequirement]:
        """Return all requirements for a given job."""
        stmt = (
            select(JobRequirement)
            .where(JobRequirement.job_id == job_id)
            .order_by(JobRequirement.importance_weight.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(
        self, requirements: list[JobRequirement],
    ) -> list[JobRequirement]:
        """Persist multiple requirements in one flush."""
        self._session.add_all(requirements)
        await self._session.flush()
        for req in requirements:
            await self._session.refresh(req)
        return requirements

    async def delete_by_job(self, job_id: uuid.UUID) -> int:
        """Remove all requirements for a given job. Returns rows deleted."""
        stmt = delete(JobRequirement).where(JobRequirement.job_id == job_id)
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
