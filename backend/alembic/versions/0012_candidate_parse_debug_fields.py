"""add candidate parse debug fields

Revision ID: 0012_parse_debug
Revises: 0011_user_page_views
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_parse_debug"
down_revision = "0011_user_page_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "raw_parsed_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "extraction_statistics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("candidate_profiles", "extraction_statistics")
    op.drop_column("candidate_profiles", "raw_parsed_data")
