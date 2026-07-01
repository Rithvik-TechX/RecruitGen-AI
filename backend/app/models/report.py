"""
Report ORM Model.

Stores generated reports with JSONB content and optional PDF file path.
"""

from __future__ import annotations

import enum
import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


# ── Enumerations ────────────────────────────────────────────


class ReportType(str, enum.Enum):
    """Types of reports that can be generated."""

    CANDIDATE = "candidate"
    HIRING = "hiring"
    MATCH = "match"
    INTERVIEW = "interview"
    ANALYTICS = "analytics"


class ReportStatus(str, enum.Enum):
    """Lifecycle states of a report."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Report ─────────────────────────────────────────────────


class Report(BaseModel):
    """Generated report entity."""

    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="report_type", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=ReportStatus.PENDING,
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────
    job: Mapped[Job | None] = relationship("Job", lazy="selectin")
    author: Mapped[User] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Report {self.report_type.value} title={self.title!r} status={self.status.value}>"
