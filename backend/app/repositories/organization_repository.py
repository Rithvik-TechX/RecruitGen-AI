"""
Organization Repository — organization-specific data access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Data access for Organization entities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Organization, session)

    async def get_by_name(self, name: str) -> Organization | None:
        """Fetch an organization by exact name (case-insensitive)."""
        stmt = select(Organization).where(
            Organization.name.ilike(name),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        """Return organization count."""
        result = await self._session.execute(select(func.count()).select_from(Organization))
        return result.scalar_one()

    async def member_counts(self, organization_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Return user counts keyed by organization ID."""
        if not organization_ids:
            return {}

        from app.models.user import User

        stmt = (
            select(User.organization_id, func.count(User.id))
            .where(User.organization_id.in_(organization_ids))
            .group_by(User.organization_id)
        )
        result = await self._session.execute(stmt)
        return {org_id: count for org_id, count in result.all()}
