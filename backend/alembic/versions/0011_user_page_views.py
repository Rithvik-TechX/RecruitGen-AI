"""create user_page_views table for badge tracking

Revision ID: 0011_user_page_views
Revises: 0010_hiring_decisions
Create Date: 2026-06-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0011_user_page_views"
down_revision = "0010_hiring_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_page_views",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("section", sa.String(100), nullable=False),
        sa.Column(
            "last_seen_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "section", name="uq_user_section"),
    )
    op.create_index("ix_user_page_views_id", "user_page_views", ["id"])


def downgrade() -> None:
    op.drop_index("ix_user_page_views_id")
    op.drop_table("user_page_views")
