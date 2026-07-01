"""
Ranking Engine Service — rank candidates with weighted scoring formula.

Scoring Formula:
    40 % Skill Match
    25 % Experience
    15 % Education
    10 % Projects
    10 % Semantic Similarity
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_ranking import CandidateRanking
from app.repositories.candidate_match_repository import CandidateMatchRepository
from app.repositories.candidate_ranking_repository import CandidateRankingRepository
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.job_repository import JobRepository

logger = structlog.get_logger(__name__)

# ── Weights ─────────────────────────────────────────────────
W_SKILL = 0.40
W_EXPERIENCE = 0.25
W_EDUCATION = 0.15
W_PROJECT = 0.10
W_SEMANTIC = 0.10


class RankingService:
    """Ranks candidates for a job using a weighted scoring formula."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ranking_repo = CandidateRankingRepository(session)
        self._match_repo = CandidateMatchRepository(session)
        self._profile_repo = CandidateProfileRepository(session)
        self._job_repo = JobRepository(session)

    async def rank_candidates(
        self, job_id: uuid.UUID,
    ) -> list[CandidateRanking]:
        """Rank all matched candidates for a job.

        Steps:
        1. Validate job exists
        2. Load match results
        3. Compute project scores per candidate
        4. Compute final weighted score
        5. Sort and persist rankings
        """
        # Validate job
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )

        # Load matches
        matches = await self._match_repo.list_by_job(job_id)
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No matches found. Run POST /api/v1/jobs/{job_id}/match first.",
            )

        # Clear old rankings
        await self._ranking_repo.delete_by_job(job_id)

        # Build ranking entries
        ranking_entries: list[dict[str, Any]] = []

        for match in matches:
            candidate = await self._profile_repo.get_by_id_with_details(
                match.candidate_id,
            )
            if not candidate:
                continue

            # Project score — based on number and relevance of projects
            project_score = self._compute_project_score(candidate)

            # Final weighted score
            final_score = (
                W_SKILL * match.skill_match_score
                + W_EXPERIENCE * match.experience_match_score
                + W_EDUCATION * match.education_match_score
                + W_PROJECT * project_score
                + W_SEMANTIC * match.semantic_similarity_score
            )

            ranking_entries.append({
                "candidate_id": candidate.id,
                "skill_score": match.skill_match_score,
                "experience_score": match.experience_match_score,
                "education_score": match.education_match_score,
                "project_score": project_score,
                "semantic_score": match.semantic_similarity_score,
                "final_score": round(final_score, 4),
                "details": {
                    "candidate_name": candidate.full_name,
                    "match_id": str(match.id),
                    "weights": {
                        "skill": W_SKILL,
                        "experience": W_EXPERIENCE,
                        "education": W_EDUCATION,
                        "project": W_PROJECT,
                        "semantic": W_SEMANTIC,
                    },
                },
            })

        # Sort by final score descending
        ranking_entries.sort(key=lambda r: r["final_score"], reverse=True)

        # Persist rankings
        for position, entry in enumerate(ranking_entries, start=1):
            ranking = CandidateRanking(
                candidate_id=entry["candidate_id"],
                job_id=job_id,
                rank_position=position,
                skill_score=entry["skill_score"],
                experience_score=entry["experience_score"],
                education_score=entry["education_score"],
                project_score=entry["project_score"],
                semantic_score=entry["semantic_score"],
                final_score=entry["final_score"],
                ranking_details=entry["details"],
            )
            await self._ranking_repo.create(ranking)

        await self._session.commit()
        logger.info(
            "ranking_complete",
            job_id=str(job_id),
            candidates_ranked=len(ranking_entries),
        )

        return await self._ranking_repo.list_by_job(job_id)

    async def get_rankings(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 100,
    ) -> list[CandidateRanking]:
        """Return stored rankings for a job."""
        return await self._ranking_repo.list_by_job(job_id, skip=skip, limit=limit)

    async def count_rankings(self, job_id: uuid.UUID) -> int:
        """Count rankings for a job."""
        return await self._ranking_repo.count_by_job(job_id)

    # ── Scoring ─────────────────────────────────────────────

    @staticmethod
    def _compute_project_score(candidate: Any) -> float:
        """Score candidate projects (0.0–1.0).

        Heuristic:
        - 0 projects → 0.0
        - 1 project  → 0.3
        - 2 projects → 0.6
        - 3+ projects → 0.8
        - Projects with descriptions get a bonus
        - Projects with technologies get a bonus
        """
        projects = candidate.projects or []
        if not projects:
            return 0.0

        count = len(projects)
        base = min(count * 0.25, 0.8)

        # Bonus for detailed projects
        detailed_bonus = 0.0
        for proj in projects:
            if proj.description and len(proj.description) > 50:
                detailed_bonus += 0.05
            if proj.technologies:
                detailed_bonus += 0.03

        return min(1.0, base + detailed_bonus)
