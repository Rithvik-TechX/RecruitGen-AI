"""
Candidate Ranking Pydantic Schemas.

Request / response validation for weighted candidate rankings per job posting.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Ranking Request / Response ──────────────────────────────


class RankRequest(BaseModel):
    """Request body to trigger candidate ranking (empty — just triggers)."""

    pass


class CandidateRankingResponse(BaseModel):
    """Public representation of a candidate's ranking for a job."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    candidate_name: str | None = None
    rank_position: int
    skill_score: float = Field(0.0, description="40% weight")
    experience_score: float = Field(0.0, description="25% weight")
    education_score: float = Field(0.0, description="15% weight")
    project_score: float = Field(0.0, description="10% weight")
    semantic_score: float = Field(0.0, description="10% weight")
    final_score: float = Field(0.0)
    ranking_details: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class RankingListResponse(BaseModel):
    """Paginated list of candidate rankings for a job."""

    job_id: uuid.UUID
    rankings: list[CandidateRankingResponse] = []
    total_count: int = 0
