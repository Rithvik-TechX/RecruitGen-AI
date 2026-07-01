"""
User Service — user-related business logic.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Handles user retrieval and profile operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Retrieve a user by ID.

        Raises:
            HTTPException 404: user not found.
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def get_by_email(self, email: str) -> User:
        """Retrieve a user by email.

        Raises:
            HTTPException 404: user not found.
        """
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user
