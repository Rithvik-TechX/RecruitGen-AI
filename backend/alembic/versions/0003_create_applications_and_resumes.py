"""create applications and resumes tables

Revision ID: 0003_apps_resumes
Revises: 0002_jobs
Create Date: 2026-06-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_apps_resumes"
down_revision = "0002_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── application_status enum ─────────────────────────────
    app_status_enum = postgresql.ENUM(
        "applied",
        "screened",
        "shortlisted",
        "interview_scheduled",
        "interview_completed",
        "selected",
        "rejected",
        name="application_status",
        create_type=False,
    )
    app_status_enum.create(op.get_bind(), checkfirst=True)

    # ── applications ────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            app_status_enum,
            nullable=False,
            server_default="applied",
        ),
        sa.Column(
            "applied_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["users.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),
    )
    op.create_index("ix_applications_id", "applications", ["id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index(
        "ix_applications_candidate_id", "applications", ["candidate_id"],
    )

    # ── resumes ─────────────────────────────────────────────
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["users.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_id", "resumes", ["id"])
    op.create_index("ix_resumes_candidate_id", "resumes", ["candidate_id"])


def downgrade() -> None:
    op.drop_table("resumes")
    op.drop_table("applications")
    postgresql.ENUM(name="application_status").drop(
        op.get_bind(), checkfirst=True,
    )
