"""create AI pipeline tables

Revision ID: 0005_ai_tables
Revises: 0004_candidates
Create Date: 2026-06-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005_ai_tables"
down_revision = "0004_candidates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── analysis_status enum ───────────────────────────────
    analysis_status_enum = postgresql.ENUM(
        "pending", "processing", "completed", "failed",
        name="analysis_status",
        create_type=False,
    )
    analysis_status_enum.create(op.get_bind(), checkfirst=True)

    # ── evaluation_type enum ───────────────────────────────
    eval_type_enum = postgresql.ENUM(
        "ai", "manual", "hybrid",
        name="evaluation_type",
        create_type=False,
    )
    eval_type_enum.create(op.get_bind(), checkfirst=True)

    # ── hiring_decision enum ───────────────────────────────
    hiring_decision_enum = postgresql.ENUM(
        "hire", "consider", "reject",
        name="hiring_decision",
        create_type=False,
    )
    hiring_decision_enum.create(op.get_bind(), checkfirst=True)

    # ── job_analyses ───────────────────────────────────────
    op.create_table(
        "job_analysiss",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("required_skills", postgresql.JSONB(), nullable=True),
        sa.Column("preferred_skills", postgresql.JSONB(), nullable=True),
        sa.Column("education_requirements", postgresql.JSONB(), nullable=True),
        sa.Column("experience_requirements", postgresql.JSONB(), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), nullable=True),
        sa.Column("analysis_summary", sa.Text(), nullable=True),
        sa.Column(
            "status", analysis_status_enum,
            nullable=False, server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_analysiss_id", "job_analysiss", ["id"])
    op.create_index("ix_job_analysiss_job_id", "job_analysiss", ["job_id"])

    # ── candidate_matchs ───────────────────────────────────
    op.create_table(
        "candidate_matchs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_match_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("experience_match_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("education_match_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("semantic_similarity_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("overall_match_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("match_details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_match_candidate_job"),
    )
    op.create_index("ix_candidate_matchs_id", "candidate_matchs", ["id"])

    # ── candidate_rankings ─────────────────────────────────
    op.create_table(
        "candidate_rankings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("experience_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("education_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("project_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("semantic_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("final_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("ranking_details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_ranking_candidate_job"),
    )
    op.create_index("ix_candidate_rankings_id", "candidate_rankings", ["id"])

    # ── skill_evaluations ──────────────────────────────────
    op.create_table(
        "skill_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("competency_scores", postgresql.JSONB(), nullable=True),
        sa.Column("skill_gaps", postgresql.JSONB(), nullable=True),
        sa.Column("strengths", postgresql.JSONB(), nullable=True),
        sa.Column("evaluation_summary", sa.Text(), nullable=True),
        sa.Column("evaluated_by", eval_type_enum, nullable=False, server_default="ai"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_eval_candidate_job"),
    )
    op.create_index("ix_skill_evaluations_id", "skill_evaluations", ["id"])

    # ── hiring_recommendations ─────────────────────────────
    op.create_table(
        "hiring_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", hiring_decision_enum, nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("risk_assessment", sa.Text(), nullable=True),
        sa.Column("strengths", postgresql.JSONB(), nullable=True),
        sa.Column("weaknesses", postgresql.JSONB(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_rec_candidate_job"),
    )
    op.create_index("ix_hiring_recommendations_id", "hiring_recommendations", ["id"])


def downgrade() -> None:
    op.drop_table("hiring_recommendations")
    op.drop_table("skill_evaluations")
    op.drop_table("candidate_rankings")
    op.drop_table("candidate_matchs")
    op.drop_table("job_analysiss")
    postgresql.ENUM(name="hiring_decision").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="evaluation_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="analysis_status").drop(op.get_bind(), checkfirst=True)
