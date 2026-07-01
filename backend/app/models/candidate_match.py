"""
CandidateMatch ORM Model.

Stores AI-computed match scores between a candidate profile and a job posting,
including component scores (skill, experience, education, semantic) and an
overall composite score.
"""

from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.candidate import CandidateProfile
    from app.models.job import Job


class CandidateMatch(BaseModel):
    """AI-computed match between a candidate and a job posting."""

    __tablename__ = "candidate_matches"


    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "job_id", name="uq_candidate_match_candidate_job",
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
    skill_match_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    experience_match_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    education_match_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    semantic_similarity_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    overall_match_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    match_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
    )

    # ── Relationships ───────────────────────────────────────
    candidate: Mapped[CandidateProfile] = relationship(
        "CandidateProfile", lazy="selectin",
    )
    job: Mapped[Job] = relationship("Job", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<CandidateMatch candidate={self.candidate_id} "
            f"job={self.job_id} overall={self.overall_match_score:.2f}>"
        )
