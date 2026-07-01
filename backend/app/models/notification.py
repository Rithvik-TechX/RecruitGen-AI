"""
Notification ORM Model.

Stores user notifications for interview invitations, shortlist alerts,
rejection notices, offer letters, and general system messages.
"""

from __future__ import annotations

import enum
import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


# ── Enumerations ────────────────────────────────────────────


class NotificationType(str, enum.Enum):
    """Categories of notifications."""

    INTERVIEW_INVITE = "interview_invite"
    SHORTLISTED = "shortlisted"
    REJECTION = "rejection"
    OFFER = "offer"
    APPLICATION_UPDATE = "application_update"
    GENERAL = "general"
    SCREENING = "screening"
    APPLICATION_SUBMITTED = "application_submitted"
    INTERVIEW_COMPLETED = "interview_completed"
    SELECTED = "selected"
    MATCHING_COMPLETED = "matching_completed"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    USER_CREATED = "user_created"
    PLATFORM_RESET = "platform_reset"
    RESUME_PARSED = "resume_parsed"


# ── Notification ───────────────────────────────────────────


class Notification(BaseModel):
    """User notification entity."""

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", values_callable=lambda enum_cls: [item.value for item in enum_cls], create_constraint=True),
        default=NotificationType.GENERAL,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True,
    )

    # ── Relationships ───────────────────────────────────────
    user: Mapped[User] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Notification {self.type.value} user={self.user_id} read={self.is_read}>"
