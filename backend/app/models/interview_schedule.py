"""
InterviewSchedule ORM Model.

Tracks scheduled interviews between candidates and interviewers
for specific job positions.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.candidate import CandidateProfile
    from app.models.job import Job
    from app.models.user import User


# ── Enumerations ────────────────────────────────────────────


class InterviewType(str, enum.Enum):
    """Type of interview."""

    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    HR = "hr"
    PANEL = "panel"


class InterviewStatus(str, enum.Enum):
    """Lifecycle states of an interview."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


# ── InterviewSchedule ──────────────────────────────────────


class InterviewSchedule(BaseModel):
    """Scheduled interview between a candidate and an interviewer."""

    __tablename__ = "interview_schedules"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False,
    )
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, name="interview_type", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=InterviewType.VIDEO,
        nullable=False,
    )
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, name="interview_status", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=InterviewStatus.SCHEDULED,
        nullable=False,
    )
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", lazy="selectin",
    )
    job: Mapped[Job] = relationship("Job", lazy="selectin")
    interviewer: Mapped[User | None] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<InterviewSchedule candidate={self.candidate_id} "
            f"job={self.job_id} status={self.status.value}>"
        )
