"""remove placeholder reports

Revision ID: 0009_real_hr_reports
Revises: 0008_research_profile
Create Date: 2026-06-13
"""

from __future__ import annotations

from alembic import op

revision = "0009_real_hr_reports"
down_revision = "0008_research_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM reports
        WHERE content ? 'report_type'
          AND content ? 'generated_at'
          AND content ? 'generated_by'
          AND (
              SELECT count(*)
              FROM jsonb_object_keys(content)
          ) = 3
        """
    )


def downgrade() -> None:
    pass
