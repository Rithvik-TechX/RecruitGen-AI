"""
Offer Letter Endpoints — generate and download offer letter PDFs.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr, get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.user import User, UserRole
from app.services.offer_service import OfferService

router = APIRouter()


async def _authorize_offer_access(
    application_id: uuid.UUID,
    current_user: User,
    session: AsyncSession,
) -> None:
    application = await session.get(Application, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.CANDIDATE:
        if application.candidate_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this offer letter.",
            )
        return

    job = await session.get(Job, application.job_id)
    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this offer letter.",
        )


@router.post(
    "/{application_id}/generate",
    summary="Generate offer letter PDF",
)
async def generate_offer_letter(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await _authorize_offer_access(application_id, current_user, session)
    service = OfferService(session)
    file_path = await service.generate_offer_letter(application_id)
    return {"status": "generated", "file_path": file_path}


@router.get(
    "/{application_id}/download",
    summary="Download offer letter PDF",
)
async def download_offer_letter(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    await _authorize_offer_access(application_id, current_user, session)
    service = OfferService(session)
    file_path = service.get_offer_path(application_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer letter not found. It may not have been generated yet.",
        )
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"offer_letter_{application_id}.pdf",
    )


@router.get(
    "/{application_id}/check",
    summary="Check if offer letter exists",
)
async def check_offer_letter(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await _authorize_offer_access(application_id, current_user, session)
    service = OfferService(session)
    file_path = service.get_offer_path(application_id)
    return {"exists": file_path is not None}
