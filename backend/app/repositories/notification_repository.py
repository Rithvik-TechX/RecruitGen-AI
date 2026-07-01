"""
Notification Repository — data access for user notifications.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Data access for Notification entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Notification, session)

    async def list_by_user(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification_id: uuid.UUID) -> Notification | None:
        notification = await self.get_by_id(notification_id)
        if notification:
            notification.is_read = True
            await self._session.flush()
            await self._session.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        result = await self._session.execute(stmt)
        return result.rowcount
