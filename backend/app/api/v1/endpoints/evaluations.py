"""
Evaluation Endpoints — AI skill evaluation.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr
from app.db.session import get_db
from app.models.user import User
from app.schemas.skill_evaluation import (
    SkillEvaluationListResponse,
    SkillEvaluationResponse,
)
from app.services.skill_evaluation_service import SkillEvaluationService

router = APIRouter()


@router.post(
    "/jobs/{job_id}/evaluate/{candidate_id}",
    response_model=SkillEvaluationResponse,
    summary="Run AI skill evaluation",
)
async def evaluate_candidate(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SkillEvaluationResponse:
    service = SkillEvaluationService(session)
    evaluation = await service.evaluate_candidate(candidate_id, job_id)
    return SkillEvaluationResponse.model_validate(evaluation)


@router.get(
    "/jobs/{job_id}/evaluations",
    response_model=SkillEvaluationListResponse,
    summary="List evaluations for a job",
)
async def list_evaluations(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> SkillEvaluationListResponse:
    service = SkillEvaluationService(session)
    evaluations, total = await service.list_by_job(job_id, skip=skip, limit=limit)
    return SkillEvaluationListResponse(
        job_id=job_id,
        evaluations=[SkillEvaluationResponse.model_validate(e) for e in evaluations],
        total_count=total,
    )
