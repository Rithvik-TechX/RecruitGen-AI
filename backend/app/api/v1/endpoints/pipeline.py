"""
Pipeline Endpoint — run the full LangGraph recruitment AI pipeline.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.langgraph.graph import run_recruitment_pipeline
from app.models.user import User

router = APIRouter()


class PipelineRequest(BaseModel):
    """Request to run the full AI pipeline."""

    resume_id: uuid.UUID
    job_id: uuid.UUID | None = None


class PipelineResponse(BaseModel):
    """Response from the AI pipeline."""

    resume_id: str | None = None
    job_id: str | None = None
    candidate_id: str | None = None
    candidate_profile: dict[str, Any] = {}
    job_analysis: dict[str, Any] = {}
    match_results: list[dict[str, Any]] = []
    ranking_results: list[dict[str, Any]] = []
    evaluation_results: dict[str, Any] = {}
    recommendation_results: dict[str, Any] = {}
    current_step: str = ""
    errors: list[str] = []
    completed: bool = False


@router.post(
    "/run",
    response_model=PipelineResponse,
    summary="Run the full recruitment AI pipeline",
)
async def run_pipeline(
    request: PipelineRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PipelineResponse:
    """Execute the complete LangGraph pipeline:

    Resume Upload → Resume Parser → Profile Builder
    → JD Analysis → Matching Engine → Ranking Engine
    """
    result = await run_recruitment_pipeline(
        session=session,
        resume_id=request.resume_id,
        job_id=request.job_id,
    )
    return PipelineResponse(**result)
