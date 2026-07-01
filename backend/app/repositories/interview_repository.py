"""
Interview Repository — data access for interview schedules.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_schedule import InterviewSchedule, InterviewStatus
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[InterviewSchedule]):
    """Data access for InterviewSchedule entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InterviewSchedule, session)

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[InterviewSchedule]:
        stmt = (
            select(InterviewSchedule)
            .where(InterviewSchedule.job_id == job_id)
            .order_by(InterviewSchedule.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_candidate(
        self, candidate_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[InterviewSchedule]:
        stmt = (
            select(InterviewSchedule)
            .where(InterviewSchedule.candidate_id == candidate_id)
            .order_by(InterviewSchedule.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_interviewer(
        self, interviewer_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[InterviewSchedule]:
        stmt = (
            select(InterviewSchedule)
            .where(InterviewSchedule.interviewer_id == interviewer_id)
            .order_by(InterviewSchedule.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_job(self, job_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(InterviewSchedule)
            .where(InterviewSchedule.job_id == job_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_status(self, status: InterviewStatus) -> int:
        stmt = (
            select(func.count())
            .select_from(InterviewSchedule)
            .where(InterviewSchedule.status == status)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
