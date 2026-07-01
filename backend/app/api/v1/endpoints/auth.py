"""
Auth Endpoints — register, login, refresh.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate account",
)
async def register(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Public registration — candidates only. Recruiter/HR accounts are created by admins."""
    if payload.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is available for candidates only. Contact an administrator for recruiter or HR accounts.",
        )
    service = AuthService(session)
    return await service.register(payload)


@router.post(
    "/admin/create-user",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin creates a recruiter or HR user",
)
async def admin_create_user(
    payload: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Admin-only endpoint to create recruiter and HR accounts."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create recruiter and HR accounts.",
        )
    service = AuthService(session)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
)
async def login(
    payload: UserLogin,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate with email + password, receive JWT token pair."""
    service = AuthService(session)
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh(
    payload: TokenRefresh,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    service = AuthService(session)
    return await service.refresh_tokens(payload.refresh_token)
