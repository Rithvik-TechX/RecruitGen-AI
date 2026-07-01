"""
JD Analysis Service — analyse job descriptions with Gemini AI.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_analysis import AnalysisStatus, JobAnalysis
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.job_repository import JobRepository
from app.providers.gemini_provider import (
    GeminiServiceError,
    analyze_jd_with_gemini,
    fallback_analyze_jd,
    mark_ai_failure,
)
from app.providers.embedding_provider import build_job_text, generate_embedding
from app.vector_store.chroma_store import VectorStore

logger = structlog.get_logger(__name__)


class JDAnalysisService:
    """Analyses job descriptions using Gemini AI."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._analysis_repo = JobAnalysisRepository(session)
        self._job_repo = JobRepository(session)

    async def analyze_job(self, job_id: uuid.UUID) -> JobAnalysis:
        """Analyse a job description and store structured results.

        Steps:
        1. Fetch job
        2. Assemble full JD text
        3. Parse with Gemini AI
        4. Store analysis results
        5. Generate & store job embedding
        """
        # 1 — Get job
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )

        # Create or reset analysis
        existing = await self._analysis_repo.get_by_job_id(job_id)
        if existing:
            analysis = existing
            analysis.analysis_status = AnalysisStatus.PROCESSING
            await self._session.flush()
        else:
            analysis = JobAnalysis(
                job_id=job_id,
                analysis_status=AnalysisStatus.PROCESSING,
            )
            analysis = await self._analysis_repo.create(analysis)

        try:
            # 2 — Build full JD text
            jd_text = job.description or ""
            # job.requirements is an ORM relationship (list of JobRequirement
            # objects), NOT a text field — iterate and build text from them.
            if job.requirements:
                req_lines = [r.skill_name for r in job.requirements]
                jd_text += "\n\nKey Skill Requirements:\n" + "\n".join(
                    f"- {line}" for line in req_lines
                )

            if not jd_text.strip():
                raise ValueError("Job has no description to analyse")

            # 3 — Analyse with Gemini, then gracefully fall back locally if AI is unavailable
            try:
                result = await analyze_jd_with_gemini(jd_text)
            except (GeminiServiceError, ValueError) as exc:
                mark_ai_failure(exc, fallback_available=True)
                logger.warning("job_ai_fallback_used", job_id=str(job_id), error=str(exc))
                result = fallback_analyze_jd(jd_text)

            # 4 — Store results
            analysis.required_skills = result.get("required_skills", [])
            analysis.preferred_skills = result.get("preferred_skills", [])
            analysis.education_requirements = result.get("education_requirements", {})
            analysis.experience_requirements = result.get("experience_requirements", {})
            analysis.keywords = result.get("keywords", [])
            analysis.analysis_summary = result.get("analysis_summary")
            analysis.analysis_status = AnalysisStatus.COMPLETED
            await self._session.flush()

            # 5 — Generate & store job embedding
            try:
                job_data = {
                    "title": job.title,
                    "description": job.description,
                }
                job_text = build_job_text(job_data, result)
                embedding = generate_embedding(job_text)
                VectorStore().upsert_job_embedding(
                    job_id=str(job_id),
                    embedding=embedding,
                    metadata={
                        "title": job.title or "",
                        "organization_id": str(job.organization_id),
                    },
                    document=job_text,
                )
            except Exception as exc:
                logger.warning("job_embedding_failed", error=str(exc))

            await self._session.commit()
            await self._session.refresh(analysis)
            logger.info("job_analyzed_successfully", job_id=str(job_id))
            return analysis

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("job_analysis_failed", job_id=str(job_id), error=str(exc))
            analysis.analysis_status = AnalysisStatus.FAILED
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyse job description: {exc}",
            ) from exc

    async def get_analysis(self, job_id: uuid.UUID) -> JobAnalysis:
        """Get job analysis by job ID."""
        analysis = await self._analysis_repo.get_by_job_id(job_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job analysis not found. Run POST /api/v1/jobs/{job_id}/analyze first.",
            )
        return analysis
