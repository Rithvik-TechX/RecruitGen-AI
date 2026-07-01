"""create candidate tables

Revision ID: 0004_candidates
Revises: 0003_apps_resumes
Create Date: 2026-06-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_candidates"
down_revision = "0003_apps_resumes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── parsing_status enum ────────────────────────────────
    parsing_status_enum = postgresql.ENUM(
        "pending", "processing", "completed", "failed",
        name="parsing_status",
        create_type=False,
    )
    parsing_status_enum.create(op.get_bind(), checkfirst=True)

    # ── candidate_profiles ─────────────────────────────────
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column(
            "parsing_status", parsing_status_enum,
            nullable=False, server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", name="uq_candidate_profile_resume"),
    )
    op.create_index("ix_candidate_profiles_id", "candidate_profiles", ["id"])
    op.create_index("ix_candidate_profiles_resume_id", "candidate_profiles", ["resume_id"])

    # ── candidate_skills ───────────────────────────────────
    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column("proficiency_level", sa.String(50), nullable=True),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_skills_id", "candidate_skills", ["id"])
    op.create_index("ix_candidate_skills_candidate_id", "candidate_skills", ["candidate_id"])

    # ── candidate_educations ───────────────────────────────
    op.create_table(
        "candidate_educations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(255), nullable=True),
        sa.Column("field_of_study", sa.String(255), nullable=True),
        sa.Column("start_date", sa.String(50), nullable=True),
        sa.Column("end_date", sa.String(50), nullable=True),
        sa.Column("gpa", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_educations_id", "candidate_educations", ["id"])
    op.create_index("ix_candidate_educations_candidate_id", "candidate_educations", ["candidate_id"])

    # ── candidate_experiences ──────────────────────────────
    op.create_table(
        "candidate_experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("start_date", sa.String(50), nullable=True),
        sa.Column("end_date", sa.String(50), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_experiences_id", "candidate_experiences", ["id"])
    op.create_index("ix_candidate_experiences_candidate_id", "candidate_experiences", ["candidate_id"])

    # ── candidate_projects ─────────────────────────────────
    op.create_table(
        "candidate_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", sa.Text(), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("start_date", sa.String(50), nullable=True),
        sa.Column("end_date", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_projects_id", "candidate_projects", ["id"])
    op.create_index("ix_candidate_projects_candidate_id", "candidate_projects", ["candidate_id"])

    # ── candidate_certifications ───────────────────────────
    op.create_table(
        "candidate_certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("certification_name", sa.String(255), nullable=False),
        sa.Column("issuing_organization", sa.String(255), nullable=True),
        sa.Column("issue_date", sa.String(50), nullable=True),
        sa.Column("expiry_date", sa.String(50), nullable=True),
        sa.Column("credential_id", sa.String(255), nullable=True),
        sa.Column("credential_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_certifications_id", "candidate_certifications", ["id"])
    op.create_index("ix_candidate_certifications_candidate_id", "candidate_certifications", ["candidate_id"])

    # ── Add missing enum values to application_status ──────
    op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'accepted'")


def downgrade() -> None:
    op.drop_table("candidate_certifications")
    op.drop_table("candidate_projects")
    op.drop_table("candidate_experiences")
    op.drop_table("candidate_educations")
    op.drop_table("candidate_skills")
    op.drop_table("candidate_profiles")
    postgresql.ENUM(name="parsing_status").drop(op.get_bind(), checkfirst=True)
