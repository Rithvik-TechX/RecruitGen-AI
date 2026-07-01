"""
Interview Service — schedule, update, and cancel interviews.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile
from app.models.interview_schedule import InterviewSchedule, InterviewStatus
from app.models.resume import Resume
from app.repositories.interview_repository import InterviewRepository
from app.schemas.interview_schedule import (
    InterviewScheduleCreate,
    InterviewScheduleUpdate,
)

logger = structlog.get_logger(__name__)


class InterviewService:
    """Manages interview scheduling lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InterviewRepository(session)

    async def schedule_interview(
        self, data: InterviewScheduleCreate,
    ) -> InterviewSchedule:
        """Create a new interview schedule."""
        interview = InterviewSchedule(
            candidate_id=data.candidate_id,
            job_id=data.job_id,
            interviewer_id=data.interviewer_id,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            interview_type=data.interview_type,
            meeting_link=data.meeting_link,
            location=data.location,
            notes=data.notes,
            status=InterviewStatus.SCHEDULED,
        )
        interview = await self._repo.create(interview)
        candidate_user_id = (
            await self._session.execute(
                select(Resume.candidate_id)
                .join(CandidateProfile, CandidateProfile.resume_id == Resume.id)
                .where(CandidateProfile.id == data.candidate_id)
            )
        ).scalar_one_or_none()
        if candidate_user_id:
            application = (
                await self._session.execute(
                    select(Application).where(
                        Application.candidate_id == candidate_user_id,
                        Application.job_id == data.job_id,
                    )
                )
            ).scalar_one_or_none()
            if application:
                application.status = ApplicationStatus.INTERVIEW_SCHEDULED
        await self._session.commit()
        logger.info(
            "interview_scheduled",
            interview_id=str(interview.id),
            candidate_id=str(data.candidate_id),
            job_id=str(data.job_id),
        )
        return interview

    async def update_interview(
        self,
        interview_id: uuid.UUID,
        data: InterviewScheduleUpdate,
    ) -> InterviewSchedule:
        """Update an existing interview."""
        interview = await self._repo.get_by_id(interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(interview, field, value)

        await self._session.flush()
        await self._session.refresh(interview)
        await self._session.commit()
        logger.info("interview_updated", interview_id=str(interview_id))
        return interview

    async def cancel_interview(self, interview_id: uuid.UUID) -> InterviewSchedule:
        """Cancel an interview."""
        interview = await self._repo.get_by_id(interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )
        interview.status = InterviewStatus.CANCELLED
        await self._session.flush()
        await self._session.refresh(interview)
        await self._session.commit()
        logger.info("interview_cancelled", interview_id=str(interview_id))
        return interview

    async def get_interview(self, interview_id: uuid.UUID) -> InterviewSchedule:
        """Fetch a single interview by ID."""
        interview = await self._repo.get_by_id(interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )
        return interview

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> tuple[list[InterviewSchedule], int]:
        """List interviews for a job with total count."""
        interviews = await self._repo.list_by_job(job_id, skip=skip, limit=limit)
        total = await self._repo.count_by_job(job_id)
        return interviews, total

    async def list_by_candidate(
        self, candidate_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> tuple[list[InterviewSchedule], int]:
        """List interviews for a candidate."""
        interviews = await self._repo.list_by_candidate(
            candidate_id, skip=skip, limit=limit
        )
        total = len(interviews)
        return interviews, total
