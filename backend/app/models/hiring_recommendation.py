"""
HiringRecommendation ORM Model.

AI-generated hiring recommendation with decision, risk assessment,
strengths/weaknesses analysis, and confidence scoring.
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


class HiringDecision(str, enum.Enum):
    """Possible hiring decisions."""

    HIRE = "hire"
    CONSIDER = "consider"
    REJECT = "reject"


# ── HiringRecommendation ──────────────────────────────────


class HiringRecommendation(BaseModel):
    """AI-generated hiring recommendation for a candidate-job pair."""

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "job_id",
            name="uq_hiring_recommendation_candidate_job",
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
    decision: Mapped[HiringDecision] = mapped_column(
        Enum(HiringDecision, name="hiring_decision", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True,
    )
    weaknesses: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True,
    )
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", lazy="selectin",
    )
    job: Mapped[Job] = relationship("Job", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<HiringRecommendation {self.decision.value} "
            f"candidate={self.candidate_id} confidence={self.confidence_score:.2f}>"
        )
