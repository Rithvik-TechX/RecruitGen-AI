"""
Job Analysis Pydantic Schemas.

Request / response validation for AI-driven job analysis: extracted skill
requirements, education / experience expectations, and keywords.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.job_analysis import AnalysisStatus


# ── Skill Requirement ───────────────────────────────────────


class SkillRequirement(BaseModel):
    """Individual skill requirement extracted from a job description."""

    name: str = Field(..., min_length=1, max_length=255)
    weight: float = Field(1.0, ge=0.0, le=10.0)
    is_required: bool = True


# ── Job Analysis ────────────────────────────────────────────


class JobAnalyzeRequest(BaseModel):
    """Request body to trigger AI job analysis (empty — just triggers)."""

    pass


class JobAnalysisResponse(BaseModel):
    """Full job analysis representation returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    required_skills: list[dict[str, Any]] | None = None
    preferred_skills: list[dict[str, Any]] | None = None
    education_requirements: dict[str, Any] | None = None
    experience_requirements: dict[str, Any] | None = None
    keywords: list[str] | None = None
    analysis_summary: str | None = None
    analysis_status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
