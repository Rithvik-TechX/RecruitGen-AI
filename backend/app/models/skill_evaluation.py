"""
SkillEvaluation ORM Model.

AI-generated technical evaluation of a candidate's skills against
a specific job's requirements.
"""

from __future__ import annotations

import enum
import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.candidate import CandidateProfile
    from app.models.job import Job


# ── Enumerations ────────────────────────────────────────────


class EvaluationType(str, enum.Enum):
    """Who / what performed the evaluation."""

    AI = "ai"
    MANUAL = "manual"
    HYBRID = "hybrid"


# ── SkillEvaluation ────────────────────────────────────────


class SkillEvaluation(BaseModel):
    """AI-powered technical skill evaluation for a candidate-job pair."""

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "job_id", name="uq_skill_evaluation_candidate_job",
        ),
    )

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
    technical_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    competency_scores: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
    )
    skill_gaps: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True,
    )
    strengths: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True,
    )
    evaluation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_by: Mapped[EvaluationType] = mapped_column(
        Enum(EvaluationType, name="evaluation_type", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=EvaluationType.AI,
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", lazy="selectin",
    )
    job: Mapped[Job] = relationship("Job", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<SkillEvaluation candidate={self.candidate_id} "
            f"job={self.job_id} score={self.technical_score:.2f}>"
        )
