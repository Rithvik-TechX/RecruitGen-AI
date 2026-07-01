"""
Interview Endpoints — schedule, update, cancel interviews.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr, get_current_user
from app.db.session import get_db
from app.models.interview_schedule import InterviewSchedule
from app.models.user import User
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.interview_schedule import (
    InterviewListResponse,
    InterviewScheduleCreate,
    InterviewScheduleResponse,
    InterviewScheduleUpdate,
)
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post(
    "/jobs/{job_id}/interviews",
    response_model=InterviewScheduleResponse,
    summary="Schedule an interview",
)
async def schedule_interview(
    job_id: uuid.UUID,
    data: InterviewScheduleCreate,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewScheduleResponse:
    service = InterviewService(session)
    data.job_id = job_id
    interview = await service.schedule_interview(data)
    return InterviewScheduleResponse.model_validate(interview)


@router.get(
    "/jobs/{job_id}/interviews",
    response_model=InterviewListResponse,
    summary="List interviews for a job",
)
async def list_interviews(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> InterviewListResponse:
    service = InterviewService(session)
    interviews, total = await service.list_by_job(job_id, skip=skip, limit=limit)
    return InterviewListResponse(
        job_id=job_id,
        interviews=[InterviewScheduleResponse.model_validate(i) for i in interviews],
        total_count=total,
    )


@router.get(
    "/interviews/me",
    response_model=list[InterviewScheduleResponse],
    summary="List my interviews (candidate view)",
)
async def list_my_interviews(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> list[InterviewScheduleResponse]:
    # Resolve User → Resume → CandidateProfile to get the correct candidate_id
    resume_repo = ResumeRepository(session)
    resume = await resume_repo.get_latest_by_candidate(current_user.id)
    if not resume:
        return []

    profile_repo = CandidateProfileRepository(session)
    profile = await profile_repo.get_by_resume_id(resume.id)
    if not profile:
        return []

    service = InterviewService(session)
    interviews, _ = await service.list_by_candidate(
        profile.id, skip=skip, limit=limit
    )
    return [InterviewScheduleResponse.model_validate(i) for i in interviews]


@router.get(
    "/interviews/by-application",
    response_model=InterviewScheduleResponse | None,
    summary="Get interview for a candidate+job combo",
)
async def get_interview_by_application(
    candidate_profile_id: uuid.UUID = Query(...),
    job_id: uuid.UUID = Query(...),
    _current_user: Annotated[User, Depends(get_current_user)] = ...,
    session: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> InterviewScheduleResponse | None:
    result = await session.execute(
        select(InterviewSchedule)
        .where(
            InterviewSchedule.candidate_id == candidate_profile_id,
            InterviewSchedule.job_id == job_id,
        )
        .order_by(InterviewSchedule.created_at.desc())
        .limit(1)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        return None
    return InterviewScheduleResponse.model_validate(interview)


@router.get(
    "/interviews/all",
    response_model=list[InterviewScheduleResponse],
    summary="List all interviews (HR/Admin)",
)
async def list_all_interviews(
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> list[InterviewScheduleResponse]:
    result = await session.execute(
        select(InterviewSchedule)
        .order_by(InterviewSchedule.scheduled_at.desc())
        .offset(skip).limit(limit)
    )
    interviews = result.scalars().all()
    return [InterviewScheduleResponse.model_validate(i) for i in interviews]


@router.patch(
    "/interviews/{interview_id}",
    response_model=InterviewScheduleResponse,
    summary="Update an interview",
)
async def update_interview(
    interview_id: uuid.UUID,
    data: InterviewScheduleUpdate,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewScheduleResponse:
    service = InterviewService(session)
    interview = await service.update_interview(interview_id, data)
    return InterviewScheduleResponse.model_validate(interview)


@router.delete(
    "/interviews/{interview_id}",
    response_model=InterviewScheduleResponse,
    summary="Cancel an interview",
)
async def cancel_interview(
    interview_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewScheduleResponse:
    service = InterviewService(session)
    interview = await service.cancel_interview(interview_id)
    return InterviewScheduleResponse.model_validate(interview)
