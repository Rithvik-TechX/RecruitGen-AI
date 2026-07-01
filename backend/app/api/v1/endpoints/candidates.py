"""
Candidate Endpoints — candidate profile retrieval.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.candidate import CandidateProfileResponse
from app.services.resume_intelligence_service import ResumeIntelligenceService

router = APIRouter()


# ── GET /candidates/me ─────────────────────────────────────
# MUST come before /{candidate_id} so FastAPI doesn't try to parse "me" as UUID

@router.get(
    "/me",
    response_model=CandidateProfileResponse | None,
    summary="Get my candidate profile",
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateProfileResponse | None:
    """Return the logged-in candidate's profile (found via their resumes).

    Returns null if no parsed profile exists yet.
    """
    service = ResumeIntelligenceService(session)
    profile = await service.get_my_profile(current_user.id)
    if not profile:
        return None
    # Only return fully-parsed profiles; failed/pending may have invalid data
    from app.models.candidate import ParsingStatus
    if profile.parsing_status != ParsingStatus.COMPLETED:
        return None
    try:
        return CandidateProfileResponse.model_validate(profile)
    except Exception:
        return None


# ── GET /candidates/by-resume/{resume_id} ───────────────────

@router.get(
    "/by-resume/{resume_id}",
    response_model=CandidateProfileResponse | None,
    summary="Get candidate profile for a resume",
)
async def get_profile_by_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateProfileResponse | None:
    """Return the parsed profile for one resume owned by the current user."""
    service = ResumeIntelligenceService(session)
    profile = await service.get_profile_by_resume(resume_id, current_user.id)
    if not profile:
        return None
    from app.models.candidate import ParsingStatus
    if profile.parsing_status != ParsingStatus.COMPLETED:
        return None
    return CandidateProfileResponse.model_validate(profile)


# ── GET /candidates/{candidate_id} ─────────────────────────

@router.get(
    "/{candidate_id}",
    response_model=CandidateProfileResponse,
    summary="Get a candidate profile",
)
async def get_candidate(
    candidate_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateProfileResponse:
    """Return a candidate profile with all parsed details."""
    service = ResumeIntelligenceService(session)
    return await service.get_candidate(candidate_id)


# ── GET /candidates ─────────────────────────────────────────

@router.get(
    "/",
    response_model=list[CandidateProfileResponse],
    summary="List all candidate profiles",
)
async def list_candidates(
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> list[CandidateProfileResponse]:
    """Return all parsed candidate profiles."""
    service = ResumeIntelligenceService(session)
    return await service.list_candidates(skip=skip, limit=limit)
