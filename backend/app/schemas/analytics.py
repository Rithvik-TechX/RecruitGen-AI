"""
Analytics Pydantic Schemas — dashboard stats, funnels, metrics.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Top-level recruitment dashboard statistics."""

    total_jobs: int = 0
    total_candidates: int = 0
    total_applications: int = 0
    shortlisted: int = 0
    rejected: int = 0
    interviews_scheduled: int = 0
    hiring_rate: float = 0.0


class FunnelStage(BaseModel):
    """Single stage in the hiring funnel."""

    stage: str
    count: int
    percentage: float = 0.0


class HiringFunnelResponse(BaseModel):
    """Hiring funnel breakdown for a job."""

    job_id: uuid.UUID
    job_title: str
    stages: list[FunnelStage]


class SkillDistribution(BaseModel):
    """Skill frequency distribution across candidates."""

    skill_name: str
    count: int
    percentage: float = 0.0


class PipelineMetrics(BaseModel):
    """Recruitment pipeline health metrics."""

    active_jobs: int = 0
    pending_reviews: int = 0
    interviews_this_week: int = 0
    avg_time_to_hire_days: float | None = None


class AnalyticsDashboardResponse(BaseModel):
    """Full analytics dashboard payload."""

    stats: DashboardStats
    pipeline: PipelineMetrics
    top_skills: list[SkillDistribution]
