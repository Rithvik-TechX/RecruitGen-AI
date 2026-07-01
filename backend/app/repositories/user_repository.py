"""
User Repository — user-specific data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for User entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_id(self, id: uuid.UUID) -> User | None:
        """Fetch a user by PK with organization eagerly loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email with organization eagerly loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.organization))
            .where(User.email == email)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
