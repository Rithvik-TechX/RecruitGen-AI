"""
Organization Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationResponse(BaseModel):
    """Public organization representation (nested in UserResponse)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    industry: str | None = None
    company_size: str | None = None
    created_at: datetime
    updated_at: datetime


class OrganizationCreate(BaseModel):
    """POST /organizations request body."""

    name: str
    industry: str | None = None
    company_size: str | None = None


class OrganizationAdminResponse(OrganizationResponse):
    """Organization representation for admin management screens."""

    member_count: int = 0


class OrganizationListResponse(BaseModel):
    """Paginated organization list."""

    organizations: list[OrganizationAdminResponse]
    total_count: int
