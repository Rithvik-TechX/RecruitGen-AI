"""
Shared API Dependencies — authentication & role-based access control.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Current User ────────────────────────────────────────────

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode JWT and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Convenience alias — ensures the user is active."""
    return current_user


# ── Role-Based Access Control ───────────────────────────────

class RoleChecker:
    """Reusable FastAPI dependency that enforces role-based access.

    Usage::

        allow_admins = RoleChecker([UserRole.ADMIN])

        @router.get("/admin-only")
        async def admin_view(
            user: Annotated[User, Depends(allow_admins)],
        ) -> dict: ...
    """

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user


# ── Pre-built Role Dependencies ─────────────────────────────

admin_only = RoleChecker([UserRole.ADMIN])
"""Dependency — only users with the **admin** role may access."""

recruiter_only = RoleChecker([UserRole.RECRUITER])
"""Dependency — only users with the **recruiter** role may access."""

candidate_only = RoleChecker([UserRole.CANDIDATE])
"""Dependency — only users with the **candidate** role may access."""

admin_or_recruiter = RoleChecker([UserRole.ADMIN, UserRole.RECRUITER])
"""Dependency — admins and recruiters may access."""

hr_manager_only = RoleChecker([UserRole.HR_MANAGER])
"""Dependency — only users with the **hr_manager** role may access."""

admin_or_hr = RoleChecker([UserRole.ADMIN, UserRole.HR_MANAGER])
"""Dependency — admins and HR managers may access."""

recruiter_or_hr = RoleChecker([UserRole.RECRUITER, UserRole.HR_MANAGER])
"""Dependency — recruiters and HR managers may access."""

admin_recruiter_or_hr = RoleChecker(
    [UserRole.ADMIN, UserRole.RECRUITER, UserRole.HR_MANAGER],
)
"""Dependency — admins, recruiters, and HR managers may access."""

