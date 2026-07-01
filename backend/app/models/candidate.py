"""
Candidate ORM Models.

Contains all candidate-related models derived from resume parsing:
- CandidateProfile  – top-level parsed profile linked to a resume
- CandidateSkill    – individual skill extracted from the resume
- CandidateEducation – education history
- CandidateExperience – work experience
- CandidateProject  – personal / professional projects
- CandidateCertification – certifications & credentials
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.resume import Resume


# ── Enumerations ────────────────────────────────────────────


class ParsingStatus(str, enum.Enum):
    """Lifecycle states of resume parsing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ParserSource(str, enum.Enum):
    """Parser implementation that produced the stored profile."""

    AI = "ai"
    FALLBACK = "fallback"


# ── CandidateProfile ───────────────────────────────────────


class CandidateProfile(BaseModel):
    """Top-level parsed candidate profile linked to an uploaded resume."""

    __table_args__ = (
        UniqueConstraint(
            "resume_id", name="uq_candidate_profile_resume",
        ),
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_parsed_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    extraction_statistics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    parser_source: Mapped[ParserSource] = mapped_column(
        Enum(
            ParserSource,
            name="parser_source",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            create_constraint=True,
        ),
        default=ParserSource.FALLBACK,
        nullable=False,
    )
    achievements: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    internships: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    awards: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    publications: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    research_experience: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    links: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    parsing_status: Mapped[ParsingStatus] = mapped_column(
        Enum(ParsingStatus, name="parsing_status", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=ParsingStatus.PENDING,
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────
    resume: Mapped[Resume] = relationship("Resume", lazy="selectin")
    skills: Mapped[list[CandidateSkill]] = relationship(
        "CandidateSkill",
        back_populates="candidate",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    education: Mapped[list[CandidateEducation]] = relationship(
        "CandidateEducation",
        back_populates="candidate",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    experiences: Mapped[list[CandidateExperience]] = relationship(
        "CandidateExperience",
        back_populates="candidate",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list[CandidateProject]] = relationship(
        "CandidateProject",
        back_populates="candidate",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    certifications: Mapped[list[CandidateCertification]] = relationship(
        "CandidateCertification",
        back_populates="candidate",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CandidateProfile {self.full_name!r} status={self.parsing_status.value}>"


# ── CandidateSkill ─────────────────────────────────────────


class CandidateSkill(BaseModel):
    """Individual skill extracted from a candidate's resume."""

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    proficiency_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_of_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", back_populates="skills",
    )

    def __repr__(self) -> str:
        return f"<CandidateSkill {self.skill_name!r} level={self.proficiency_level}>"


# ── CandidateEducation ─────────────────────────────────────


class CandidateEducation(BaseModel):
    """Education record extracted from a candidate's resume."""

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gpa: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", back_populates="education",
    )

    def __repr__(self) -> str:
        return f"<CandidateEducation {self.institution!r} degree={self.degree}>"


# ── CandidateExperience ────────────────────────────────────


class CandidateExperience(BaseModel):
    """Work experience record extracted from a candidate's resume."""

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", back_populates="experiences",
    )

    def __repr__(self) -> str:
        return f"<CandidateExperience {self.company!r} title={self.title!r}>"


# ── CandidateProject ──────────────────────────────────────


class CandidateProject(BaseModel):
    """Personal or professional project extracted from a candidate's resume."""

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", back_populates="projects",
    )

    def __repr__(self) -> str:
        return f"<CandidateProject {self.project_name!r}>"


# ── CandidateCertification ────────────────────────────────


class CandidateCertification(BaseModel):
    """Certification or credential extracted from a candidate's resume."""

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    certification_name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", back_populates="certifications",
    )

    def __repr__(self) -> str:
        return f"<CandidateCertification {self.certification_name!r}>"
