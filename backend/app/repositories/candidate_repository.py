"""
Candidate Repository — data access for candidate profiles and sub-entities.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate import (
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateProfile,
    CandidateProject,
    CandidateSkill,
)
from app.repositories.base import BaseRepository


class CandidateProfileRepository(BaseRepository[CandidateProfile]):
    """Data access for CandidateProfile entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateProfile, session)

    async def get_by_id_with_details(
        self, profile_id: uuid.UUID,
    ) -> CandidateProfile | None:
        """Fetch a candidate profile with all related data eagerly loaded."""
        stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.id == profile_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(CandidateProfile.skills),
                selectinload(CandidateProfile.education),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.projects),
                selectinload(CandidateProfile.certifications),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_resume_id(
        self, resume_id: uuid.UUID,
    ) -> CandidateProfile | None:
        """Fetch candidate profile by resume ID with all details."""
        stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.resume_id == resume_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(CandidateProfile.skills),
                selectinload(CandidateProfile.education),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.projects),
                selectinload(CandidateProfile.certifications),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all_with_details(
        self, *, skip: int = 0, limit: int = 100,
    ) -> list[CandidateProfile]:
        """Return all candidate profiles with details eagerly loaded."""
        stmt = (
            select(CandidateProfile)
            .options(
                selectinload(CandidateProfile.skills),
                selectinload(CandidateProfile.education),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.projects),
                selectinload(CandidateProfile.certifications),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id(
        self, user_id: uuid.UUID,
    ) -> CandidateProfile | None:
        """Find the most recent candidate profile for a user.

        Joins through Resume (resume.candidate_id == user.id) to find
        the CandidateProfile linked to that resume.
        """
        from app.models.resume import Resume

        stmt = (
            select(CandidateProfile)
            .join(Resume, CandidateProfile.resume_id == Resume.id)
            .where(Resume.candidate_id == user_id)
            .options(
                selectinload(CandidateProfile.skills),
                selectinload(CandidateProfile.education),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.projects),
                selectinload(CandidateProfile.certifications),
            )
            .order_by(Resume.uploaded_at.desc(), CandidateProfile.updated_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class CandidateSkillRepository(BaseRepository[CandidateSkill]):
    """Data access for CandidateSkill entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateSkill, session)

    async def list_by_candidate(
        self, candidate_id: uuid.UUID,
    ) -> list[CandidateSkill]:
        """Return skills for a given candidate."""
        stmt = select(CandidateSkill).where(
            CandidateSkill.candidate_id == candidate_id,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(
        self, skills: list[CandidateSkill],
    ) -> list[CandidateSkill]:
        """Persist multiple skills in one flush."""
        self._session.add_all(skills)
        await self._session.flush()
        return skills


class CandidateEducationRepository(BaseRepository[CandidateEducation]):
    """Data access for CandidateEducation entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateEducation, session)

    async def bulk_create(
        self, educations: list[CandidateEducation],
    ) -> list[CandidateEducation]:
        """Persist multiple education records in one flush."""
        self._session.add_all(educations)
        await self._session.flush()
        return educations


class CandidateExperienceRepository(BaseRepository[CandidateExperience]):
    """Data access for CandidateExperience entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateExperience, session)

    async def bulk_create(
        self, experiences: list[CandidateExperience],
    ) -> list[CandidateExperience]:
        """Persist multiple experience records in one flush."""
        self._session.add_all(experiences)
        await self._session.flush()
        return experiences


class CandidateProjectRepository(BaseRepository[CandidateProject]):
    """Data access for CandidateProject entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateProject, session)

    async def bulk_create(
        self, projects: list[CandidateProject],
    ) -> list[CandidateProject]:
        """Persist multiple project records in one flush."""
        self._session.add_all(projects)
        await self._session.flush()
        return projects


class CandidateCertificationRepository(BaseRepository[CandidateCertification]):
    """Data access for CandidateCertification entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CandidateCertification, session)

    async def bulk_create(
        self, certifications: list[CandidateCertification],
    ) -> list[CandidateCertification]:
        """Persist multiple certification records in one flush."""
        self._session.add_all(certifications)
        await self._session.flush()
        return certifications
