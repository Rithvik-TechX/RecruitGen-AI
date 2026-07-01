"""create jobs and job_requirements tables

Revision ID: 0002_jobs
Revises: 0001_orgs_users
Create Date: 2026-06-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_jobs"
down_revision = "0001_orgs_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── job_status enum ─────────────────────────────────────
    job_status_enum = postgresql.ENUM(
        "draft", "active", "closed",
        name="job_status",
        create_type=False,
    )
    job_status_enum.create(op.get_bind(), checkfirst=True)

    # ── jobs ────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(150), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("experience_required", sa.String(100), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            job_status_enum,
            nullable=False,
            server_default="draft",
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
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recruiter_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"])
    op.create_index("ix_jobs_organization_id", "jobs", ["organization_id"])
    op.create_index("ix_jobs_recruiter_id", "jobs", ["recruiter_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # ── job_requirements ────────────────────────────────────
    op.create_table(
        "job_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("skill_name", sa.String(200), nullable=False),
        sa.Column(
            "importance_weight",
            sa.Float(),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column("required_level", sa.String(50), nullable=False),
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
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_requirements_id", "job_requirements", ["id"])
    op.create_index(
        "ix_job_requirements_job_id", "job_requirements", ["job_id"],
    )


def downgrade() -> None:
    op.drop_table("job_requirements")
    op.drop_table("jobs")
    postgresql.ENUM(name="job_status").drop(op.get_bind(), checkfirst=True)
