"""
Report Repository — data access for generated reports.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Data access for Report entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Report, session)

    async def list_by_user(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.generated_by == user_id)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.job_id == job_id)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Report)
            .where(Report.generated_by == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
