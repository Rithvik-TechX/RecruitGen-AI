"""expand candidate profile resume data

Revision ID: 0007_resume_profile
Revises: 0006_remaining
Create Date: 2026-06-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_resume_profile"
down_revision = "0006_remaining"
branch_labels = None
depends_on = None


def upgrade() -> None:
    parser_source_enum = postgresql.ENUM(
        "ai",
        "fallback",
        name="parser_source",
        create_type=False,
    )
    parser_source_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "candidate_profiles",
        sa.Column(
            "parser_source",
            parser_source_enum,
            nullable=False,
            server_default="fallback",
        ),
    )
    for column_name in (
        "achievements",
        "internships",
        "awards",
        "publications",
        "languages",
        "links",
    ):
        op.add_column(
            "candidate_profiles",
            sa.Column(
                column_name,
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )


def downgrade() -> None:
    for column_name in (
        "links",
        "languages",
        "publications",
        "awards",
        "internships",
        "achievements",
    ):
        op.drop_column("candidate_profiles", column_name)
    op.drop_column("candidate_profiles", "parser_source")
    postgresql.ENUM(name="parser_source").drop(op.get_bind(), checkfirst=True)
