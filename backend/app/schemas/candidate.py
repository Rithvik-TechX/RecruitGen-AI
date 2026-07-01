"""
Candidate Pydantic Schemas.

Request / response validation for candidate profiles and all related
sub-entities (skills, education, experience, projects, certifications).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.candidate import ParserSource, ParsingStatus


# ── CandidateSkill ──────────────────────────────────────────


class CandidateSkillBase(BaseModel):
    """Shared fields for candidate skill schemas."""

    skill_name: str = Field(..., min_length=1, max_length=255)
    proficiency_level: str | None = Field(None, max_length=50)
    years_of_experience: float | None = Field(None, ge=0)
    category: str | None = Field(None, max_length=100)


class CandidateSkillCreate(CandidateSkillBase):
    """Payload for creating a candidate skill."""

    pass


class CandidateSkillResponse(CandidateSkillBase):
    """Public representation of a candidate skill."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── CandidateEducation ──────────────────────────────────────


class CandidateEducationBase(BaseModel):
    """Shared fields for candidate education schemas."""

    institution: str = Field(..., min_length=1, max_length=255)
    degree: str | None = Field(None, max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    start_date: str | None = Field(None, max_length=50)
    end_date: str | None = Field(None, max_length=50)
    gpa: str | None = Field(None, max_length=20)
    description: str | None = None


class CandidateEducationCreate(CandidateEducationBase):
    """Payload for creating a candidate education record."""

    pass


class CandidateEducationResponse(CandidateEducationBase):
    """Public representation of a candidate education record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── CandidateExperience ─────────────────────────────────────


class CandidateExperienceBase(BaseModel):
    """Shared fields for candidate experience schemas."""

    company: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    location: str | None = Field(None, max_length=255)
    start_date: str | None = Field(None, max_length=50)
    end_date: str | None = Field(None, max_length=50)
    is_current: bool = False
    description: str | None = None
    technologies: str | None = None


class CandidateExperienceCreate(CandidateExperienceBase):
    """Payload for creating a candidate experience record."""

    pass


class CandidateExperienceResponse(CandidateExperienceBase):
    """Public representation of a candidate experience record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── CandidateProject ────────────────────────────────────────


class CandidateProjectBase(BaseModel):
    """Shared fields for candidate project schemas."""

    project_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    technologies: str | None = None
    year: str | None = Field(None, max_length=20)
    url: str | None = Field(None, max_length=500)
    start_date: str | None = Field(None, max_length=50)
    end_date: str | None = Field(None, max_length=50)


class CandidateProjectCreate(CandidateProjectBase):
    """Payload for creating a candidate project record."""

    pass


class CandidateProjectResponse(CandidateProjectBase):
    """Public representation of a candidate project record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── CandidateCertification ──────────────────────────────────


class CandidateCertificationBase(BaseModel):
    """Shared fields for candidate certification schemas."""

    certification_name: str = Field(..., min_length=1, max_length=255)
    issuing_organization: str | None = Field(None, max_length=255)
    issue_date: str | None = Field(None, max_length=50)
    expiry_date: str | None = Field(None, max_length=50)
    credential_id: str | None = Field(None, max_length=255)
    credential_url: str | None = Field(None, max_length=500)


class CandidateCertificationCreate(CandidateCertificationBase):
    """Payload for creating a candidate certification record."""

    pass


class CandidateCertificationResponse(CandidateCertificationBase):
    """Public representation of a candidate certification record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CandidateAchievement(BaseModel):
    title: str
    description: str | None = None
    date: str | None = None


class CandidateInternship(BaseModel):
    company: str
    role: str
    duration: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class CandidateAward(BaseModel):
    title: str
    issuer: str | None = None
    date: str | None = None
    description: str | None = None


class CandidatePublication(BaseModel):
    title: str
    publisher: str | None = None
    publication_date: str | None = None
    url: str | None = None
    description: str | None = None


class CandidateLink(BaseModel):
    link_type: str
    label: str | None = None
    url: str


class CandidateResearchExperience(BaseModel):
    title: str
    description: str | None = None
    duration: str | None = None


# ── CandidateProfile ────────────────────────────────────────


class CandidateProfileBase(BaseModel):
    """Shared fields for candidate profile schemas."""

    full_name: str = Field(..., min_length=1, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)
    summary: str | None = None


class CandidateProfileCreate(CandidateProfileBase):
    """Payload for creating a candidate profile."""

    resume_id: uuid.UUID
    raw_text: str | None = None
    skills: list[CandidateSkillCreate] = Field(default_factory=list)
    education: list[CandidateEducationCreate] = Field(default_factory=list)
    experiences: list[CandidateExperienceCreate] = Field(default_factory=list)
    projects: list[CandidateProjectCreate] = Field(default_factory=list)
    certifications: list[CandidateCertificationCreate] = Field(default_factory=list)
    achievements: list[CandidateAchievement] = Field(default_factory=list)
    internships: list[CandidateInternship] = Field(default_factory=list)
    awards: list[CandidateAward] = Field(default_factory=list)
    publications: list[CandidatePublication] = Field(default_factory=list)
    research_experience: list[CandidateResearchExperience] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    links: list[CandidateLink] = Field(default_factory=list)


class CandidateProfileResponse(CandidateProfileBase):
    """Full candidate profile representation returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    raw_text: str | None = None
    raw_parsed_data: dict = Field(default_factory=dict)
    extraction_statistics: dict[str, int] = Field(default_factory=dict)
    parsing_status: ParsingStatus
    parser_source: ParserSource
    skills: list[CandidateSkillResponse] = Field(default_factory=list)
    education: list[CandidateEducationResponse] = Field(default_factory=list)
    experiences: list[CandidateExperienceResponse] = Field(default_factory=list)
    projects: list[CandidateProjectResponse] = Field(default_factory=list)
    certifications: list[CandidateCertificationResponse] = Field(default_factory=list)
    achievements: list[CandidateAchievement] = Field(default_factory=list)
    internships: list[CandidateInternship] = Field(default_factory=list)
    awards: list[CandidateAward] = Field(default_factory=list)
    publications: list[CandidatePublication] = Field(default_factory=list)
    research_experience: list[CandidateResearchExperience] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    links: list[CandidateLink] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ── Resume Parsing Requests / Responses ─────────────────────


class ResumeParseRequest(BaseModel):
    """Request body to trigger resume parsing."""

    pass


class ResumeParseResponse(BaseModel):
    """Response after initiating resume parsing."""

    candidate_id: uuid.UUID
    status: ParsingStatus
    parser_source: ParserSource
    statistics: dict[str, int]
    message: str
