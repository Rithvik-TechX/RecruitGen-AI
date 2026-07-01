"""
Interview Schedule Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview_schedule import InterviewStatus, InterviewType


class InterviewScheduleCreate(BaseModel):
    """Request to schedule an interview."""

    candidate_id: uuid.UUID
    job_id: uuid.UUID
    interviewer_id: uuid.UUID | None = None
    scheduled_at: datetime
    duration_minutes: int = Field(60, ge=15, le=480)
    interview_type: InterviewType = InterviewType.VIDEO
    meeting_link: str | None = None
    location: str | None = None
    notes: str | None = None


class InterviewScheduleUpdate(BaseModel):
    """Request to update an interview."""

    status: InterviewStatus | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(None, ge=15, le=480)
    meeting_link: str | None = None
    notes: str | None = None
    feedback: str | None = None


class InterviewScheduleResponse(BaseModel):
    """Full interview schedule representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    interviewer_id: uuid.UUID | None = None
    scheduled_at: datetime
    duration_minutes: int
    interview_type: InterviewType
    status: InterviewStatus
    meeting_link: str | None = None
    location: str | None = None
    notes: str | None = None
    feedback: str | None = None
    created_at: datetime
    updated_at: datetime


class InterviewListResponse(BaseModel):
    """Paginated interview list."""

    job_id: uuid.UUID
    interviews: list[InterviewScheduleResponse]
    total_count: int
