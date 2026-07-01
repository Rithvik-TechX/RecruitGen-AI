"""add research experience and project year

Revision ID: 0008_research_profile
Revises: 0007_resume_profile
Create Date: 2026-06-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_research_profile"
down_revision = "0007_resume_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "research_experience",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "candidate_projects",
        sa.Column("year", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidate_projects", "year")
    op.drop_column("candidate_profiles", "research_experience")
