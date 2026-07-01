"""
Analytics Endpoints — dashboard, funnel, skills, pipeline.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    DashboardStats,
    HiringFunnelResponse,
    PipelineMetrics,
    SkillDistribution,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=AnalyticsDashboardResponse, summary="Dashboard stats")
async def dashboard(
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsDashboardResponse:
    service = AnalyticsService(session)
    stats = await service.get_dashboard_stats(current_user.organization_id)
    pipeline = await service.get_pipeline_metrics(current_user.organization_id)
    top_skills = await service.get_skill_distribution(current_user.organization_id)
    return AnalyticsDashboardResponse(
        stats=DashboardStats(**stats),
        pipeline=PipelineMetrics(**pipeline),
        top_skills=[SkillDistribution(**s) for s in top_skills],
    )


@router.get("/funnel/{job_id}", response_model=HiringFunnelResponse, summary="Hiring funnel")
async def hiring_funnel(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> HiringFunnelResponse:
    service = AnalyticsService(session)
    data = await service.get_hiring_funnel(job_id)
    return HiringFunnelResponse(**data)


@router.get("/skills", response_model=list[SkillDistribution], summary="Skill distribution")
async def skill_distribution(
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[SkillDistribution]:
    service = AnalyticsService(session)
    data = await service.get_skill_distribution(current_user.organization_id)
    return [SkillDistribution(**s) for s in data]


@router.get("/pipeline", response_model=PipelineMetrics, summary="Pipeline metrics")
async def pipeline_metrics(
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PipelineMetrics:
    service = AnalyticsService(session)
    data = await service.get_pipeline_metrics(current_user.organization_id)
    return PipelineMetrics(**data)
