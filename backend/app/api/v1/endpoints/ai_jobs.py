"""
AI Job Endpoints — JD analysis, matching, and ranking.

All endpoints are nested under /jobs/{job_id}/... to follow
REST conventions alongside the existing jobs router.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.job_analysis import JobAnalysisResponse
from app.schemas.candidate_match import CandidateMatchResponse, MatchListResponse
from app.schemas.candidate_ranking import CandidateRankingResponse, RankingListResponse
from app.services.jd_analysis_service import JDAnalysisService
from app.services.matching_service import MatchingService
from app.services.ranking_service import RankingService

router = APIRouter()


# ═══════════════════════════════════════════════════════════
# JD ANALYSIS
# ═══════════════════════════════════════════════════════════

@router.post(
    "/{job_id}/analyze",
    response_model=JobAnalysisResponse,
    summary="Analyse a job description with AI",
    tags=["AI - Job Analysis"],
)
async def analyze_job(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobAnalysisResponse:
    """Trigger AI-powered analysis of a job description.

    Extracts required skills, preferred skills, education requirements,
    experience requirements, and keywords.
    """
    service = JDAnalysisService(session)
    return await service.analyze_job(job_id)


@router.get(
    "/{job_id}/analysis",
    response_model=JobAnalysisResponse,
    summary="Get job analysis results",
    tags=["AI - Job Analysis"],
)
async def get_analysis(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobAnalysisResponse:
    """Return stored AI analysis for a job."""
    service = JDAnalysisService(session)
    return await service.get_analysis(job_id)


# ═══════════════════════════════════════════════════════════
# MATCHING
# ═══════════════════════════════════════════════════════════

@router.post(
    "/{job_id}/match",
    response_model=MatchListResponse,
    summary="Match candidates to a job",
    tags=["AI - Matching"],
)
async def match_candidates(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MatchListResponse:
    """Match ALL candidate profiles against a job and compute scores."""
    service = MatchingService(session)
    matches = await service.match_candidates_to_job(job_id)
    total = await service.count_matches(job_id)
    return MatchListResponse(
        job_id=job_id,
        matches=[
            CandidateMatchResponse(
                id=m.id,
                candidate_id=m.candidate_id,
                job_id=m.job_id,
                candidate_name=m.candidate.full_name if m.candidate else "",
                skill_match_score=m.skill_match_score,
                experience_match_score=m.experience_match_score,
                education_match_score=m.education_match_score,
                semantic_similarity_score=m.semantic_similarity_score,
                overall_match_score=m.overall_match_score,
                match_details=m.match_details,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in matches
        ],
        total_count=total,
    )


@router.get(
    "/{job_id}/matches",
    response_model=MatchListResponse,
    summary="Get match results for a job",
    tags=["AI - Matching"],
)
async def get_matches(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> MatchListResponse:
    """Return stored match results for a job."""
    service = MatchingService(session)
    matches = await service.get_matches(job_id, skip=skip, limit=limit)
    total = await service.count_matches(job_id)
    return MatchListResponse(
        job_id=job_id,
        matches=[
            CandidateMatchResponse(
                id=m.id,
                candidate_id=m.candidate_id,
                job_id=m.job_id,
                candidate_name=m.candidate.full_name if m.candidate else "",
                skill_match_score=m.skill_match_score,
                experience_match_score=m.experience_match_score,
                education_match_score=m.education_match_score,
                semantic_similarity_score=m.semantic_similarity_score,
                overall_match_score=m.overall_match_score,
                match_details=m.match_details,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in matches
        ],
        total_count=total,
    )


# ═══════════════════════════════════════════════════════════
# RANKING
# ═══════════════════════════════════════════════════════════

@router.post(
    "/{job_id}/rank",
    response_model=RankingListResponse,
    summary="Rank candidates for a job",
    tags=["AI - Ranking"],
)
async def rank_candidates(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RankingListResponse:
    """Rank matched candidates using the weighted scoring formula."""
    service = RankingService(session)
    rankings = await service.rank_candidates(job_id)
    total = await service.count_rankings(job_id)
    return RankingListResponse(
        job_id=job_id,
        rankings=[
            CandidateRankingResponse(
                id=r.id,
                candidate_id=r.candidate_id,
                job_id=r.job_id,
                candidate_name=r.candidate.full_name if r.candidate else "",
                rank_position=r.rank_position,
                skill_score=r.skill_score,
                experience_score=r.experience_score,
                education_score=r.education_score,
                project_score=r.project_score,
                semantic_score=r.semantic_score,
                final_score=r.final_score,
                ranking_details=r.ranking_details,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rankings
        ],
        total_count=total,
    )


@router.get(
    "/{job_id}/rankings",
    response_model=RankingListResponse,
    summary="Get ranking results for a job",
    tags=["AI - Ranking"],
)
async def get_rankings(
    job_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> RankingListResponse:
    """Return stored ranking results for a job."""
    service = RankingService(session)
    rankings = await service.get_rankings(job_id, skip=skip, limit=limit)
    total = await service.count_rankings(job_id)
    return RankingListResponse(
        job_id=job_id,
        rankings=[
            CandidateRankingResponse(
                id=r.id,
                candidate_id=r.candidate_id,
                job_id=r.job_id,
                candidate_name=r.candidate.full_name if r.candidate else "",
                rank_position=r.rank_position,
                skill_score=r.skill_score,
                experience_score=r.experience_score,
                education_score=r.education_score,
                project_score=r.project_score,
                semantic_score=r.semantic_score,
                final_score=r.final_score,
                ranking_details=r.ranking_details,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rankings
        ],
        total_count=total,
    )
