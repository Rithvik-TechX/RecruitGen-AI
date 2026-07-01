"""
Hiring Recommendation Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.hiring_recommendation import HiringDecision


class HiringRecommendationResponse(BaseModel):
    """Full hiring recommendation representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    decision: HiringDecision
    confidence_score: float
    risk_assessment: str | None = None
    strengths: list[dict[str, Any]] | None = None
    weaknesses: list[dict[str, Any]] | None = None
    reasoning: str | None = None
    summary: str | None = None
    candidate_name: str | None = None
    created_at: datetime
    updated_at: datetime


class HiringRecommendationListResponse(BaseModel):
    """Paginated recommendation list."""

    job_id: uuid.UUID
    recommendations: list[HiringRecommendationResponse]
    total_count: int
