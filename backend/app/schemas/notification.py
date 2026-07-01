"""
Notification Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """Full notification representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool
    metadata_: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    notifications: list[NotificationResponse]
    unread_count: int
    total_count: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""

    count: int
