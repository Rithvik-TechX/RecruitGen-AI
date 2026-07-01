"""
UserPageView ORM Model.

Tracks per-user, per-section "last seen" timestamps for badge counts.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class UserPageView(BaseModel):
    """Tracks when a user last viewed a specific page/section."""

    __table_args__ = (
        UniqueConstraint("user_id", "section", name="uq_user_section"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
