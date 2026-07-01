"""
Candidate Ranking Repository — data access for weighted rankings.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate_ranking import CandidateRanking
from app.repositories.base import BaseRepository


class CandidateRankingRepository(BaseRepository[CandidateRanking]):
    """Data access for CandidateRanking entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateRanking, session)

    async def list_by_job(
        self,
        job_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CandidateRanking]:
        """Return rankings for a job, ordered by rank position asc."""
        stmt = (
            select(CandidateRanking)
            .where(CandidateRanking.job_id == job_id)
            .options(selectinload(CandidateRanking.candidate))
            .order_by(CandidateRanking.rank_position.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_candidate_and_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> CandidateRanking | None:
        """Fetch a ranking for a specific candidate-job pair."""
        stmt = select(CandidateRanking).where(
            CandidateRanking.candidate_id == candidate_id,
            CandidateRanking.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_job(self, job_id: uuid.UUID) -> int:
        """Remove all rankings for a given job. Returns rows deleted."""
        stmt = delete(CandidateRanking).where(CandidateRanking.job_id == job_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def count_by_job(self, job_id: uuid.UUID) -> int:
        """Count rankings for a job."""
        stmt = select(func.count(CandidateRanking.id)).where(
            CandidateRanking.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
