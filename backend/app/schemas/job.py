"""
Job & JobRequirement Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


# ── JobRequirement ──────────────────────────────────────────

class JobRequirementCreate(BaseModel):
    """Payload for adding a skill requirement to a job."""

    skill_name: str = Field(..., min_length=1, max_length=200)
    importance_weight: float = Field(1.0, ge=0.0, le=10.0)
    required_level: str = Field(..., min_length=1, max_length=50)


class JobRequirementResponse(BaseModel):
    """Public representation of a job requirement."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    skill_name: str
    importance_weight: float
    required_level: str


# ── Job ─────────────────────────────────────────────────────

class JobCreate(BaseModel):
    """POST /jobs request body."""

    title: str = Field(..., min_length=1, max_length=255)
    department: str | None = Field(None, max_length=150)
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = Field(None, max_length=50)
    experience_required: str | None = Field(None, max_length=100)
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    description: str | None = None
    status: JobStatus = JobStatus.DRAFT


class JobUpdate(BaseModel):
    """PUT /jobs/{id} request body — all fields optional."""

    title: str | None = Field(None, min_length=1, max_length=255)
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    experience_required: str | None = None
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    description: str | None = None
    status: JobStatus | None = None


class JobResponse(BaseModel):
    """Full job representation returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    recruiter_id: uuid.UUID
    title: str
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    experience_required: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    description: str | None = None
    status: JobStatus
    requirements: list[JobRequirementResponse] = []
    created_at: datetime
    updated_at: datetime
