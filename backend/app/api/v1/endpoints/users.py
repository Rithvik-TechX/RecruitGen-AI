"""
User Endpoints — current user profile + admin user management.
"""

from __future__ import annotations

from typing import Annotated

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import admin_only, get_current_active_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
)
async def list_users(
    _current_user: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[UserResponse]:
    """Return all users in the system (admin only)."""
    stmt = (
        select(User)
        .options(selectinload(User.organization))
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = list(result.scalars().all())
    return [UserResponse.model_validate(u) for u in users]


@router.patch(
    "/{user_id}/toggle-active",
    response_model=UserResponse,
    summary="Enable or disable a user account (admin only)",
)
async def toggle_user_active(
    user_id: uuid.UUID,
    _current_user: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Toggle a user's is_active status. Admin only."""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot disable admin accounts.",
        )
    user.is_active = not user.is_active
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a user account (admin only)",
)
async def delete_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Permanently remove a non-admin user account. Admin only."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete your own admin account.",
        )

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be permanently deleted from this screen.",
        )

    await session.delete(user)
    await session.commit()
