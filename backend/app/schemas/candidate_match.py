"""
Candidate Match Pydantic Schemas.

Request / response validation for AI-computed candidate–job match scores.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Score Breakdown ─────────────────────────────────────────


class MatchScoreBreakdown(BaseModel):
    """Component-level match score breakdown."""

    skill_match_score: float = Field(0.0, ge=0.0)
    experience_match_score: float = Field(0.0, ge=0.0)
    education_match_score: float = Field(0.0, ge=0.0)
    semantic_similarity_score: float = Field(0.0, ge=0.0)
    overall_match_score: float = Field(0.0, ge=0.0)


# ── Match Request / Response ────────────────────────────────


class MatchRequest(BaseModel):
    """Request body to trigger candidate–job matching (empty — just triggers)."""

    pass


class CandidateMatchResponse(BaseModel):
    """Public representation of a candidate–job match result."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    candidate_name: str | None = None
    skill_match_score: float
    experience_match_score: float
    education_match_score: float
    semantic_similarity_score: float
    overall_match_score: float
    match_details: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class MatchListResponse(BaseModel):
    """Paginated list of match results for a job."""

    job_id: uuid.UUID
    matches: list[CandidateMatchResponse] = []
    total_count: int = 0
