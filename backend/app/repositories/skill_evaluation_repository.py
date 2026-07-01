"""
Skill Evaluation Repository — data access for AI skill evaluations.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_evaluation import SkillEvaluation
from app.repositories.base import BaseRepository


class SkillEvaluationRepository(BaseRepository[SkillEvaluation]):
    """Data access for SkillEvaluation entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SkillEvaluation, session)

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[SkillEvaluation]:
        stmt = (
            select(SkillEvaluation)
            .where(SkillEvaluation.job_id == job_id)
            .order_by(SkillEvaluation.technical_score.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_candidate_and_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> SkillEvaluation | None:
        stmt = select(SkillEvaluation).where(
            SkillEvaluation.candidate_id == candidate_id,
            SkillEvaluation.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_job(self, job_id: uuid.UUID) -> int:
        stmt = delete(SkillEvaluation).where(SkillEvaluation.job_id == job_id)
        result = await self._session.execute(stmt)
        return result.rowcount

    async def count_by_job(self, job_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(SkillEvaluation)
            .where(SkillEvaluation.job_id == job_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
