"""
User Pydantic Schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole
from app.schemas.organization import OrganizationResponse


class UserResponse(BaseModel):
    """Public user representation returned by API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    organization: OrganizationResponse | None = None
    created_at: datetime
    updated_at: datetime
