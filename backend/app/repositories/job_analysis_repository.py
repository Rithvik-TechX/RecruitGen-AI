"""
Job Analysis Repository — data access for AI-generated job analyses.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_analysis import JobAnalysis
from app.repositories.base import BaseRepository


class JobAnalysisRepository(BaseRepository[JobAnalysis]):
    """Data access for JobAnalysis entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(JobAnalysis, session)

    async def get_by_job_id(self, job_id: uuid.UUID) -> JobAnalysis | None:
        """Fetch a job analysis by its job_id."""
        stmt = select(JobAnalysis).where(JobAnalysis.job_id == job_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
