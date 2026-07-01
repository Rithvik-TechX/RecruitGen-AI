"""
Candidate Match Repository — data access for AI-computed match scores.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate_match import CandidateMatch
from app.repositories.base import BaseRepository


class CandidateMatchRepository(BaseRepository[CandidateMatch]):
    """Data access for CandidateMatch entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateMatch, session)

    async def list_by_job(
        self,
        job_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CandidateMatch]:
        """Return matches for a job, ordered by overall score desc."""
        stmt = (
            select(CandidateMatch)
            .where(CandidateMatch.job_id == job_id)
            .options(selectinload(CandidateMatch.candidate))
            .order_by(CandidateMatch.overall_match_score.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_candidate_and_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> CandidateMatch | None:
        """Fetch a match for a specific candidate-job pair."""
        stmt = select(CandidateMatch).where(
            CandidateMatch.candidate_id == candidate_id,
            CandidateMatch.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_job(self, job_id: uuid.UUID) -> int:
        """Remove all matches for a given job. Returns rows deleted."""
        stmt = delete(CandidateMatch).where(CandidateMatch.job_id == job_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def count_by_job(self, job_id: uuid.UUID) -> int:
        """Count matches for a job."""
        stmt = select(func.count(CandidateMatch.id)).where(
            CandidateMatch.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
