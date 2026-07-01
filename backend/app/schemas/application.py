"""
Application Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    """POST /applications request body."""

    job_id: uuid.UUID


class ApplicationStatusUpdate(BaseModel):
    """PATCH /applications/{id}/status request body."""

    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    """Public application representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    selected_at: datetime | None = None
    selected_by: uuid.UUID | None = None
    rejected_at: datetime | None = None
    rejected_by: uuid.UUID | None = None
    candidate_name: str | None = None
    job_title: str | None = None
    candidate_profile_id: uuid.UUID | None = None
    overall_match_score: float | None = None
    skill_match_score: float | None = None
    experience_match_score: float | None = None
    rank_position: int | None = None
    final_score: float | None = None
