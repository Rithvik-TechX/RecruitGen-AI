"""
Skill Evaluation Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.skill_evaluation import EvaluationType


class SkillEvaluationResponse(BaseModel):
    """Full skill evaluation representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    technical_score: float
    competency_scores: dict[str, Any] | None = None
    skill_gaps: list[dict[str, Any]] | None = None
    strengths: list[str] | None = None
    evaluation_summary: str | None = None
    evaluated_by: EvaluationType
    created_at: datetime
    updated_at: datetime


class SkillEvaluationListResponse(BaseModel):
    """Paginated evaluation list."""

    job_id: uuid.UUID
    evaluations: list[SkillEvaluationResponse]
    total_count: int
