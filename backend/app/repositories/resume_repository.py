"""
Resume Repository — resume-specific data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    """Data access for Resume entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Resume, session)

    async def list_by_candidate(
        self,
        candidate_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Resume]:
        """Return all resumes uploaded by a candidate (newest first)."""
        stmt = (
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_candidate(
        self, candidate_id: uuid.UUID,
    ) -> Resume | None:
        """Return the most recently uploaded resume for a candidate."""
        stmt = (
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.uploaded_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
