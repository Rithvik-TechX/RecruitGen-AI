"""
Job & JobRequirement ORM Models.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class JobStatus(str, enum.Enum):
    """Lifecycle states of a job posting."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class Job(BaseModel):
    """Job posting created by a recruiter within an organization."""

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(150), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experience_required: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[float | None] = mapped_column(
        Numeric(12, 2, asdecimal=False), nullable=True,
    )
    salary_max: Mapped[float | None] = mapped_column(
        Numeric(12, 2, asdecimal=False), nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            create_constraint=True,
        ),
        default=JobStatus.DRAFT,
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────
    organization: Mapped[Organization] = relationship(
        "Organization", lazy="selectin",
    )
    recruiter: Mapped[User] = relationship(
        "User", lazy="selectin",
    )
    requirements: Mapped[list[JobRequirement]] = relationship(
        "JobRequirement",
        back_populates="job",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Job {self.title!r} status={self.status.value}>"


class JobRequirement(BaseModel):
    """Skill / competency requirement attached to a job posting."""

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    importance_weight: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False,
    )
    required_level: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Relationships ───────────────────────────────────────
    job: Mapped[Job] = relationship("Job", back_populates="requirements")

    def __repr__(self) -> str:
        return f"<JobRequirement {self.skill_name!r} level={self.required_level}>"
