"""
Resume Endpoints — upload and retrieval.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import candidate_only
from app.db.session import get_db
from app.models.user import User
from app.schemas.resume import ResumeResponse
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume",
)
async def upload_resume(
    file: UploadFile,
    current_user: Annotated[User, Depends(candidate_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeResponse:
    """Upload a resume file (PDF, DOC, DOCX — max 10 MB)."""
    service = ResumeService(session)
    resume = await service.upload(file, current_user)
    return ResumeResponse.model_validate(resume)


@router.get(
    "/me",
    response_model=list[ResumeResponse],
    summary="My resumes",
)
async def get_my_resumes(
    current_user: Annotated[User, Depends(candidate_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ResumeResponse]:
    """List all resumes uploaded by the current candidate."""
    service = ResumeService(session)
    resumes = await service.list_my_resumes(
        current_user, skip=skip, limit=limit,
    )
    return [ResumeResponse.model_validate(r) for r in resumes]
