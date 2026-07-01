"""create interviews, notifications, reports tables

Revision ID: 0006_remaining
Revises: 0005_ai_tables
Create Date: 2026-06-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_remaining"
down_revision = "0005_ai_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── interview enums ────────────────────────────────────
    interview_type_enum = postgresql.ENUM(
        "phone", "video", "onsite", "technical", "hr", "panel",
        name="interview_type",
        create_type=False,
    )
    interview_type_enum.create(op.get_bind(), checkfirst=True)

    interview_status_enum = postgresql.ENUM(
        "scheduled", "confirmed", "in_progress", "completed",
        "cancelled", "no_show", "rescheduled",
        name="interview_status",
        create_type=False,
    )
    interview_status_enum.create(op.get_bind(), checkfirst=True)

    # ── notification_type enum ─────────────────────────────
    notification_type_enum = postgresql.ENUM(
        "interview_invite", "shortlisted", "rejection", "offer",
        "application_update", "general",
        name="notification_type",
        create_type=False,
    )
    notification_type_enum.create(op.get_bind(), checkfirst=True)

    # ── report enums ───────────────────────────────────────
    report_type_enum = postgresql.ENUM(
        "candidate", "hiring", "match", "interview", "analytics",
        name="report_type",
        create_type=False,
    )
    report_type_enum.create(op.get_bind(), checkfirst=True)

    report_status_enum = postgresql.ENUM(
        "pending", "generating", "completed", "failed",
        name="report_status",
        create_type=False,
    )
    report_status_enum.create(op.get_bind(), checkfirst=True)

    # ── interview_schedules ────────────────────────────────
    op.create_table(
        "interview_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("interview_type", interview_type_enum, nullable=False, server_default="video"),
        sa.Column("status", interview_status_enum, nullable=False, server_default="scheduled"),
        sa.Column("meeting_link", sa.String(500), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_schedules_id", "interview_schedules", ["id"])
    op.create_index("ix_interview_schedules_job_id", "interview_schedules", ["job_id"])
    op.create_index("ix_interview_schedules_candidate_id", "interview_schedules", ["candidate_id"])

    # ── notifications ──────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", notification_type_enum, nullable=False, server_default="general"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── reports ────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_type", report_type_enum, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", postgresql.JSONB(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("status", report_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_id", "reports", ["id"])
    op.create_index("ix_reports_generated_by", "reports", ["generated_by"])


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("notifications")
    op.drop_table("interview_schedules")
    postgresql.ENUM(name="report_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="report_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="notification_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="interview_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="interview_type").drop(op.get_bind(), checkfirst=True)
