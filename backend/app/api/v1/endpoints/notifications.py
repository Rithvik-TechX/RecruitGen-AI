"""
Notification Endpoints — list, read, unread count.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.communication_service import CommunicationService

router = APIRouter()


@router.get("/", response_model=NotificationListResponse, summary="List my notifications")
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> NotificationListResponse:
    service = CommunicationService(session)
    notifications, unread, total = await service.list_notifications(
        current_user.id, skip=skip, limit=limit,
    )
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        unread_count=unread,
        total_count=total,
    )


@router.get("/unread-count", response_model=UnreadCountResponse, summary="Unread count")
async def unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UnreadCountResponse:
    service = CommunicationService(session)
    count = await service.get_unread_count(current_user.id)
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark as read")
async def mark_read(
    notification_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationResponse:
    service = CommunicationService(session)
    notification = await service.mark_read(notification_id)
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read", summary="Mark all notifications as read")
async def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = CommunicationService(session)
    count = await service.mark_all_read(current_user.id)
    return {"status": "ok", "marked": count}

