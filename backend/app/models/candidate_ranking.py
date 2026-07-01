"""
CandidateRanking ORM Model.

Stores the final weighted ranking of a candidate for a specific job posting.
Score components:
- skill_score      (40 % weight)
- experience_score (25 % weight)
- education_score  (15 % weight)
- project_score    (10 % weight)
- semantic_score   (10 % weight)
"""

from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.candidate import CandidateProfile
    from app.models.job import Job


class CandidateRanking(BaseModel):
    """Weighted ranking of a candidate for a job, with score breakdown."""

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "job_id", name="uq_candidate_ranking_candidate_job",
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
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    experience_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    education_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    project_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    semantic_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    final_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    ranking_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
    )

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", lazy="selectin",
    )
    job: Mapped[Job] = relationship("Job", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<CandidateRanking #{self.rank_position} "
            f"candidate={self.candidate_id} job={self.job_id} "
            f"final={self.final_score:.2f}>"
        )
