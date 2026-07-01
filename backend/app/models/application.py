"""
Application ORM Model.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class ApplicationStatus(str, enum.Enum):
    """Lifecycle stages of a job application."""

    APPLIED = "applied"
    SCREENED = "screened"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    SELECTED = "selected"
    REJECTED = "rejected"


class Application(BaseModel):
    """A candidate's application to a specific job posting."""

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "job_id", name="uq_candidate_job",
        ),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=ApplicationStatus.APPLIED,
        nullable=False,
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    selected_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )
    selected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ───────────────────────────────────────
    job: Mapped[Job] = relationship("Job", lazy="selectin")
    candidate: Mapped[User] = relationship(
        "User", foreign_keys=[candidate_id], lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Application job={self.job_id} candidate={self.candidate_id} status={self.status.value}>"
