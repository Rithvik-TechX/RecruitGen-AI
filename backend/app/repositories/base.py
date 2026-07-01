"""
Base Repository — generic async CRUD operations.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """Generic async repository with common CRUD operations."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelT | None:
        """Fetch a single record by primary key."""
        return await self._session.get(self._model, id)

    async def create(self, obj: ModelT) -> ModelT:
        """Persist a new record and return it refreshed."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def list_all(
        self, *, skip: int = 0, limit: int = 100,
    ) -> list[ModelT]:
        """Return a paginated list of records."""
        stmt = select(self._model).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, obj: ModelT) -> None:
        """Remove a record from the session."""
        await self._session.delete(obj)
        await self._session.flush()
