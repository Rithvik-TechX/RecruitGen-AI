"""
Authentication Service — register, login, refresh.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserCreate, UserLogin

logger = structlog.get_logger(__name__)


class AuthService:
    """Handles registration, login, and token refresh."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._org_repo = OrganizationRepository(session)

    # ── helpers ─────────────────────────────────────────────

    @staticmethod
    def _build_token_pair(user: User) -> TokenResponse:
        """Create access + refresh token pair for a user."""
        payload = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(payload),
            refresh_token=create_refresh_token(payload),
        )

    # ── public API ──────────────────────────────────────────

    async def register(self, payload: UserCreate) -> TokenResponse:
        """Register a new user (and organization if needed).

        Raises:
            HTTPException 409: email already taken.
        """
        # Duplicate email guard
        if await self._user_repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        # Resolve or create organization
        organization = await self._org_repo.get_by_name(payload.organization_name)
        if not organization:
            organization = Organization(
                name=payload.organization_name,
                industry=payload.industry,
                company_size=payload.company_size,
            )
            organization = await self._org_repo.create(organization)

        # Create user
        user = User(
            organization_id=organization.id,
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )
        user = await self._user_repo.create(user)
        await self._session.commit()
        await self._session.refresh(user)

        logger.info(
            "user_registered",
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            organization=organization.name,
        )

        return self._build_token_pair(user)

    async def login(self, payload: UserLogin) -> TokenResponse:
        """Authenticate a user and return a token pair.

        Raises:
            HTTPException 401: invalid credentials.
            HTTPException 403: account deactivated.
        """
        user = await self._user_repo.get_by_email(payload.email)

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated.",
            )

        logger.info("user_logged_in", user_id=str(user.id), email=user.email)

        return self._build_token_pair(user)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Issue a new token pair from a valid refresh token.

        Raises:
            HTTPException 401: invalid / expired refresh token or user gone.
        """
        token_data = decode_token(refresh_token)
        if not token_data or token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self._user_repo.get_by_id(uuid.UUID(token_data["sub"]))

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated.",
            )

        logger.info("token_refreshed", user_id=str(user.id))

        return self._build_token_pair(user)
