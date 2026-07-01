"""Typed schemas for presentation-ready recruitment reports."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportStatus, ReportType


class ReportCreate(BaseModel):
    job_id: uuid.UUID | None = None
    report_type: ReportType
    title: str


class ReportHeader(BaseModel):
    organization_name: str
    generated_date: datetime
    report_period: str


class HiringSummary(BaseModel):
    total_jobs: int = 0
    total_applications: int = 0
    screened: int = 0
    shortlisted: int = 0
    interviewed: int = 0
    selected: int = 0
    rejected: int = 0


class AnalyticsSummary(BaseModel):
    applications: int = 0
    conversion_rate: float = 0
    average_match_score: float = 0
    average_skill_score: float = 0


class MatchSummary(BaseModel):
    total_matches: int = 0
    average_overall_score: float = 0


class FunnelStage(BaseModel):
    stage: str
    count: int


class ChartPoint(BaseModel):
    label: str
    value: float


class CandidateInsight(BaseModel):
    candidate_name: str
    job_applied: str
    match_score: float | None = None
    skill_score: float | None = None
    recommendation: str | None = None
    status: str


class RecommendationSummary(BaseModel):
    hire: int = 0
    consider: int = 0
    reject: int = 0


class SkillInsight(BaseModel):
    skill_name: str
    count: int


class MatchInsight(BaseModel):
    candidate: str
    overall_score: float = 0
    skill_score: float = 0
    experience_score: float = 0
    education_score: float = 0
    semantic_score: float = 0


class HiringReportData(BaseModel):
    kind: Literal["hiring"] = "hiring"
    header: ReportHeader
    summary: HiringSummary
    pipeline: list[FunnelStage]
    candidates: list[CandidateInsight]
    recommendation_summary: RecommendationSummary
    top_skills: list[SkillInsight]
    executive_summary: str


class AnalyticsReportData(BaseModel):
    kind: Literal["analytics"] = "analytics"
    header: ReportHeader
    summary: AnalyticsSummary
    application_trend: list[ChartPoint]
    status_distribution: list[ChartPoint]
    recommendation_distribution: list[ChartPoint]
    match_score_distribution: list[ChartPoint]
    executive_summary: str


class MatchReportData(BaseModel):
    kind: Literal["match"] = "match"
    header: ReportHeader
    summary: MatchSummary
    matches: list[MatchInsight]
    executive_summary: str


class GenericReportData(BaseModel):
    kind: Literal["generic"] = "generic"
    header: ReportHeader
    executive_summary: str


ReportData = HiringReportData | AnalyticsReportData | MatchReportData | GenericReportData


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_type: ReportType
    title: str
    summary: str | None = None
    data: ReportData = Field(discriminator="kind")
    status: ReportStatus
    created_at: datetime
    updated_at: datetime


class ReportListItem(BaseModel):
    id: uuid.UUID
    report_type: ReportType
    title: str
    summary: str | None = None
    organization_name: str
    report_period: str
    status: ReportStatus
    created_at: datetime


class ReportListResponse(BaseModel):
    reports: list[ReportListItem]
    total_count: int
