"""
JobAnalysis ORM Model.

Stores AI-parsed analysis of a job posting: extracted skill requirements,
education / experience expectations, keywords, and overall summary.
"""

from __future__ import annotations

import enum
import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.job import Job


# ── Enumerations ────────────────────────────────────────────


class AnalysisStatus(str, enum.Enum):
    """Lifecycle states of a job analysis."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── JobAnalysis ─────────────────────────────────────────────


class JobAnalysis(BaseModel):
    """AI-generated structured analysis of a job posting."""

    __tablename__ = "job_analyses"


    __table_args__ = (
        UniqueConstraint(
            "job_id", name="uq_job_analysis_job",
        ),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    required_skills: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True,
    )
    preferred_skills: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True,
    )
    education_requirements: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
    )
    experience_requirements: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
    )
    keywords: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True,
    )
    analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────
    job: Mapped[Job] = relationship("Job", lazy="selectin")

    def __repr__(self) -> str:
        return f"<JobAnalysis job={self.job_id} status={self.analysis_status.value}>"
