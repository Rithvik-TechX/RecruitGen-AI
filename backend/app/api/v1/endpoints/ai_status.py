"""AI Status Endpoint."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.providers.gemini_provider import get_ai_status

router = APIRouter()


@router.get("/status", summary="Get AI provider status")
async def ai_status(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return the current AI provider health state."""
    return get_ai_status()
