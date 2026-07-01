"""add hiring decision columns and notification types

Revision ID: 0010_hiring_decisions
Revises: 0009_real_hr_reports
Create Date: 2026-06-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0010_hiring_decisions"
down_revision = "0009_real_hr_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add hiring decision tracking columns to applications
    op.add_column(
        "applications",
        sa.Column("selected_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column(
            "selected_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "applications",
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column(
            "rejected_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Expand notification type enum with new values
    # PostgreSQL ALTER TYPE ... ADD VALUE is not transactional, so we run
    # each outside the current transaction block.
    notification_values = [
        "screening",
        "application_submitted",
        "interview_completed",
        "selected",
        "matching_completed",
        "recommendation_generated",
        "user_created",
        "platform_reset",
        "resume_parsed",
    ]
    for val in notification_values:
        op.execute(
            f"ALTER TYPE notification_type ADD VALUE IF NOT EXISTS '{val}'"
        )


def downgrade() -> None:
    op.drop_column("applications", "rejected_by")
    op.drop_column("applications", "rejected_at")
    op.drop_column("applications", "selected_by")
    op.drop_column("applications", "selected_at")
