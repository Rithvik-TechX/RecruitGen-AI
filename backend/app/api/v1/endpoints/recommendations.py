"""
Recommendation Endpoints — AI hiring recommendations.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr
from app.db.session import get_db
from app.models.user import User
from app.schemas.hiring_recommendation import (
    HiringRecommendationListResponse,
    HiringRecommendationResponse,
)
from app.services.hiring_recommendation_service import HiringRecommendationService

router = APIRouter()


@router.post(
    "/jobs/{job_id}/recommend/{candidate_id}",
    response_model=HiringRecommendationResponse,
    summary="Generate hiring recommendation",
)
async def recommend(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> HiringRecommendationResponse:
    service = HiringRecommendationService(session)
    rec = await service.recommend(candidate_id, job_id)
    resp = HiringRecommendationResponse.model_validate(rec)
    if rec.candidate:
        resp.candidate_name = rec.candidate.full_name
    return resp


@router.get(
    "/jobs/{job_id}/recommendations",
    response_model=HiringRecommendationListResponse,
    summary="List recommendations for a job",
)
async def list_recommendations(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> HiringRecommendationListResponse:
    service = HiringRecommendationService(session)
    recs, total = await service.list_by_job(job_id, skip=skip, limit=limit)
    responses = []
    for r in recs:
        resp = HiringRecommendationResponse.model_validate(r)
        if r.candidate:
            resp.candidate_name = r.candidate.full_name
        responses.append(resp)
    return HiringRecommendationListResponse(
        job_id=job_id,
        recommendations=responses,
        total_count=total,
    )
