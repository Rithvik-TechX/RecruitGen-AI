"""
Organization Endpoints - admin organization management.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_only
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    OrganizationAdminResponse,
    OrganizationCreate,
    OrganizationListResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=OrganizationListResponse,
    summary="List organizations",
)
async def list_organizations(
    _current_user: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> OrganizationListResponse:
    """Return all organizations with member counts."""
    repo = OrganizationRepository(session)
    organizations = await repo.list_all(skip=skip, limit=limit)
    counts = await repo.member_counts([org.id for org in organizations])
    total = await repo.count_all()

    return OrganizationListResponse(
        organizations=[
            OrganizationAdminResponse.model_validate(org).model_copy(
                update={"member_count": counts.get(org.id, 0)},
            )
            for org in organizations
        ],
        total_count=total,
    )


@router.post(
    "/",
    response_model=OrganizationAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
)
async def create_organization(
    payload: OrganizationCreate,
    _current_user: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> OrganizationAdminResponse:
    """Create a new organization."""
    repo = OrganizationRepository(session)
    existing = await repo.get_by_name(payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An organization with this name already exists.",
        )

    organization = await repo.create(
        Organization(
            name=payload.name,
            industry=payload.industry,
            company_size=payload.company_size,
        ),
    )
    await session.commit()
    await session.refresh(organization)
    return OrganizationAdminResponse.model_validate(organization).model_copy(
        update={"member_count": 0},
    )
