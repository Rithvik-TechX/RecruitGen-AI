"""
Hiring Recommendation Repository — data access for AI hiring recommendations.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hiring_recommendation import HiringDecision, HiringRecommendation
from app.repositories.base import BaseRepository


class HiringRecommendationRepository(BaseRepository[HiringRecommendation]):
    """Data access for HiringRecommendation entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(HiringRecommendation, session)

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[HiringRecommendation]:
        stmt = (
            select(HiringRecommendation)
            .where(HiringRecommendation.job_id == job_id)
            .order_by(HiringRecommendation.confidence_score.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_candidate_and_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> HiringRecommendation | None:
        stmt = select(HiringRecommendation).where(
            HiringRecommendation.candidate_id == candidate_id,
            HiringRecommendation.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_job(self, job_id: uuid.UUID) -> int:
        stmt = delete(HiringRecommendation).where(
            HiringRecommendation.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def count_by_decision(
        self, job_id: uuid.UUID, decision: HiringDecision,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(HiringRecommendation)
            .where(
                HiringRecommendation.job_id == job_id,
                HiringRecommendation.decision == decision,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
