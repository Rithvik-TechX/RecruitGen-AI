"""
Candidate Endpoints — resume parsing & candidate retrieval.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.candidate import (
    CandidateProfileResponse,
    ResumeParseResponse,
)
from app.services.resume_intelligence_service import ResumeIntelligenceService

router = APIRouter()


# ── POST /resumes/parse/{resume_id} ────────────────────────

@router.post(
    "/parse/{resume_id}",
    response_model=ResumeParseResponse,
    summary="Parse a resume and build a candidate profile",
)
async def parse_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeParseResponse:
    """Trigger AI-powered resume parsing for a given resume ID.

    Extracts personal details, skills, education, experience, projects,
    and certifications, then stores them as a structured candidate profile.
    """
    service = ResumeIntelligenceService(session)
    await service.get_profile_by_resume(resume_id, current_user.id)
    profile = await service.parse_resume(resume_id)
    return ResumeParseResponse(
        candidate_id=profile.id,
        status=profile.parsing_status,
        parser_source=profile.parser_source,
        statistics=profile.extraction_statistics,
        message="Resume parsed successfully.",
    )
