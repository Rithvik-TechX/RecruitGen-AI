"""
Authentication Pydantic Schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """POST /auth/register request body."""

    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    organization_name: str = Field(..., min_length=1, max_length=255)
    industry: str | None = Field(None, max_length=255)
    company_size: str | None = Field(None, max_length=50)
    role: UserRole = UserRole.CANDIDATE


class UserLogin(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned on login / register / refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """POST /auth/refresh request body."""

    refresh_token: str
