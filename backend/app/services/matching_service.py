"""
Matching Engine Service — compute match scores between candidates and jobs.
"""

from __future__ import annotations

import uuid
import re
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateProfile
from app.models.candidate_match import CandidateMatch
from app.repositories.candidate_match_repository import CandidateMatchRepository
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.job_repository import JobRepository
from app.providers.embedding_provider import compute_cosine_similarity
from app.vector_store.chroma_store import VectorStore

logger = structlog.get_logger(__name__)


class MatchingService:
    """Computes multi-dimensional match scores between candidates and jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._match_repo = CandidateMatchRepository(session)
        self._profile_repo = CandidateProfileRepository(session)
        self._job_repo = JobRepository(session)
        self._analysis_repo = JobAnalysisRepository(session)

    # ── Public API ──────────────────────────────────────────

    async def match_candidates_to_job(
        self, job_id: uuid.UUID,
    ) -> list[CandidateMatch]:
        """Match ALL candidates against a specific job.

        Steps:
        1. Load job + analysis
        2. Load all candidate profiles
        3. For each candidate, compute 4 scores
        4. Persist CandidateMatch records
        """
        # Validate job
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )

        # Require analysis
        analysis = await self._analysis_repo.get_by_job_id(job_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job has not been analysed. Run POST /api/v1/jobs/{job_id}/analyze first.",
            )

        # Load candidates
        candidates = await self._profile_repo.list_all_with_details()
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No candidate profiles found.",
            )

        # Clear old matches
        await self._match_repo.delete_by_job(job_id)

        matches: list[CandidateMatch] = []
        try:
            vector_store: VectorStore | None = VectorStore()
        except Exception as exc:
            logger.warning("vector_store_unavailable_for_matching", error=str(exc))
            vector_store = None

        for candidate in candidates:
            scores = self._compute_match_scores(candidate, analysis, job, vector_store)

            match = CandidateMatch(
                candidate_id=candidate.id,
                job_id=job_id,
                skill_match_score=scores["skill"],
                experience_match_score=scores["experience"],
                education_match_score=scores["education"],
                semantic_similarity_score=scores["semantic"],
                overall_match_score=scores["overall"],
                match_details=scores["details"],
            )
            match = await self._match_repo.create(match)
            matches.append(match)

        await self._session.commit()
        logger.info(
            "matching_complete",
            job_id=str(job_id),
            candidates_matched=len(matches),
        )

        return await self._match_repo.list_by_job(job_id)

    async def get_matches(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 100,
    ) -> list[CandidateMatch]:
        """Return stored matches for a job."""
        return await self._match_repo.list_by_job(job_id, skip=skip, limit=limit)

    async def count_matches(self, job_id: uuid.UUID) -> int:
        """Count matches for a job."""
        return await self._match_repo.count_by_job(job_id)

    # ── Scoring Logic ───────────────────────────────────────

    def _compute_match_scores(
        self,
        candidate: CandidateProfile,
        analysis: Any,
        job: Any,
        vector_store: VectorStore | None,
    ) -> dict[str, Any]:
        """Compute all match sub-scores for a candidate-job pair."""
        skill_score = self._compute_skill_score(candidate, analysis)
        exp_score = self._compute_experience_score(candidate, analysis)
        edu_score = self._compute_education_score(candidate, analysis)
        project_score = self._compute_project_score(candidate, analysis)
        certification_score = self._compute_certification_score(candidate, analysis)
        achievement_score = self._compute_achievement_score(candidate, analysis)
        semantic_score = self._compute_semantic_score(
            str(candidate.id), str(job.id), vector_store,
        )

        overall = (
            0.40 * skill_score
            + 0.20 * exp_score
            + 0.15 * project_score
            + 0.10 * edu_score
            + 0.10 * certification_score
            + 0.05 * achievement_score
        )
        if overall == 0.0 and semantic_score > 0:
            overall = min(0.25, semantic_score * 0.25)

        matched_skills = self._get_matched_skills(candidate, analysis)
        missing_skills = self._get_missing_skills(candidate, analysis)
        strengths = self._build_strength_areas(
            skill_score,
            exp_score,
            project_score,
            edu_score,
            certification_score,
            achievement_score,
        )

        logger.info(
            "candidate_match_debug",
            candidate_id=str(candidate.id),
            job_id=str(job.id),
            skill_overlap=len(matched_skills),
            missing_skills=len(missing_skills),
            experience_score=round(exp_score, 4),
            project_score=round(project_score, 4),
            certification_score=round(certification_score, 4),
            final_score=round(overall, 4),
        )

        return {
            "skill": round(skill_score, 4),
            "experience": round(exp_score, 4),
            "education": round(edu_score, 4),
            "semantic": round(semantic_score, 4),
            "overall": round(overall, 4),
            "details": {
                "formula": {
                    "skills": 0.40,
                    "experience": 0.20,
                    "projects": 0.15,
                    "education": 0.10,
                    "certifications": 0.10,
                    "achievements": 0.05,
                },
                "skill_matched": matched_skills,
                "missing_skills": missing_skills,
                "strength_areas": strengths,
                "recommendation": self._match_recommendation(overall),
                "project_score": round(project_score, 4),
                "certification_score": round(certification_score, 4),
                "achievement_score": round(achievement_score, 4),
                "semantic_similarity_observed": round(semantic_score, 4),
                "total_required_skills": len(analysis.required_skills or []),
                "total_candidate_skills": len(candidate.skills),
                "experience_years_estimated": self._estimate_years(candidate),
            },
        }

    def _compute_skill_score(
        self, candidate: CandidateProfile, analysis: Any,
    ) -> float:
        """Skill match: weighted overlap between candidate skills and job requirements."""
        required = analysis.required_skills or []
        preferred = analysis.preferred_skills or []

        if not required and not preferred:
            return 0.5  # no skills to match against

        candidate_skills_lower = self._candidate_terms(candidate)

        # When fallback parser extracted few skills, also search raw resume text
        raw_text_lower = (candidate.raw_text or "").lower()

        total_weight = 0.0
        matched_weight = 0.0

        for skill in required:
            weight = float(skill.get("weight", 1.0))
            total_weight += weight
            name = skill.get("name", "").lower()
            # Check parsed skills first, then fall back to raw text search
            if any(name in cs or cs in name for cs in candidate_skills_lower):
                matched_weight += weight
            elif raw_text_lower and name in raw_text_lower:
                matched_weight += weight * 0.8  # slightly lower confidence for raw text match

        for skill in preferred:
            weight = float(skill.get("weight", 0.5)) * 0.5  # half importance
            total_weight += weight
            name = skill.get("name", "").lower()
            if any(name in cs or cs in name for cs in candidate_skills_lower):
                matched_weight += weight
            elif raw_text_lower and name in raw_text_lower:
                matched_weight += weight * 0.8

        return matched_weight / total_weight if total_weight > 0 else 0.0

    def _compute_experience_score(
        self, candidate: CandidateProfile, analysis: Any,
    ) -> float:
        """Experience match: compare estimated years against requirements."""
        req = analysis.experience_requirements or {}
        min_years = req.get("minimum_years", 0)
        pref_years = req.get("preferred_years", 0)
        target = max(min_years, pref_years, 1)

        estimated = self._estimate_years(candidate)
        if estimated == 0 and candidate.experiences:
            estimated = float(len(candidate.experiences))

        if estimated >= target:
            return 1.0
        elif estimated >= min_years:
            return 0.5 + 0.5 * (estimated - min_years) / max(target - min_years, 1)
        else:
            return max(0.0, estimated / target) if target > 0 else 0.0

    def _compute_education_score(
        self, candidate: CandidateProfile, analysis: Any,
    ) -> float:
        """Education match: check degree alignment with requirements."""
        req = analysis.education_requirements or {}
        min_degree = (req.get("minimum_degree") or "").lower()
        preferred_fields = [f.lower() for f in req.get("preferred_fields", [])]

        if not min_degree and not preferred_fields:
            return 0.5  # no education requirements

        score = 0.0
        degree_hierarchy = {
            "phd": 4, "doctorate": 4,
            "master": 3, "mba": 3, "ms": 3, "ma": 3,
            "bachelor": 2, "bs": 2, "ba": 2, "btech": 2, "be": 2,
            "associate": 1, "diploma": 1,
        }

        target_level = 0
        for key, level in degree_hierarchy.items():
            if key in min_degree:
                target_level = level
                break

        best_candidate_level = 0
        field_match = False
        for edu in candidate.education:
            degree = (edu.degree or "").lower()
            field = (edu.field_of_study or "").lower()

            for key, level in degree_hierarchy.items():
                if key in degree:
                    best_candidate_level = max(best_candidate_level, level)
                    break

            if preferred_fields and any(pf in field or field in pf for pf in preferred_fields):
                field_match = True

        # Degree level score (60%)
        if target_level > 0:
            degree_score = min(1.0, best_candidate_level / target_level)
        else:
            degree_score = 1.0 if best_candidate_level > 0 else 0.5

        # Field match score (40%)
        field_score = 1.0 if field_match else 0.3 if not preferred_fields else 0.0

        score = 0.6 * degree_score + 0.4 * field_score
        return score

    def _compute_project_score(self, candidate: CandidateProfile, analysis: Any) -> float:
        """Project match: compare project text with required/preferred skills."""
        projects = candidate.projects or []
        if not projects:
            return 0.0
        requirements = self._requirement_names(analysis)
        if not requirements:
            return min(1.0, len(projects) / 2)
        project_text = " ".join(
            " ".join(str(value or "") for value in (
                project.project_name,
                project.description,
                project.technologies,
            ))
            for project in projects
        ).lower()
        matched = sum(1 for skill in requirements if self._term_matches_text(skill, project_text))
        breadth = min(1.0, len(projects) / 3)
        overlap = matched / len(requirements)
        return min(1.0, 0.70 * overlap + 0.30 * breadth)

    def _compute_certification_score(self, candidate: CandidateProfile, analysis: Any) -> float:
        """Certification match: reward relevant credentials and credential breadth."""
        certifications = candidate.certifications or []
        if not certifications:
            return 0.0
        requirements = self._requirement_names(analysis)
        cert_text = " ".join(
            " ".join(str(value or "") for value in (
                cert.certification_name,
                cert.issuing_organization,
            ))
            for cert in certifications
        ).lower()
        if not requirements:
            return min(1.0, len(certifications) / 2)
        matched = sum(1 for skill in requirements if self._term_matches_text(skill, cert_text))
        breadth = min(1.0, len(certifications) / 3)
        return min(1.0, 0.65 * (matched / len(requirements)) + 0.35 * breadth)

    @staticmethod
    def _compute_achievement_score(candidate: CandidateProfile, analysis: Any) -> float:
        """Achievement match: reward valid achievement evidence without overpowering skills."""
        achievement_count = len(candidate.achievements or []) + len(candidate.awards or []) + len(candidate.publications or [])
        research_count = len(candidate.research_experience or [])
        if achievement_count == 0 and research_count == 0:
            return 0.0
        return min(1.0, (achievement_count * 0.25) + (research_count * 0.20))

    def _compute_semantic_score(
        self,
        candidate_id: str,
        job_id: str,
        vector_store: VectorStore,
    ) -> float:
        """Semantic similarity: cosine similarity between embeddings."""
        try:
            if vector_store is None:
                return 0.0

            candidate_data = vector_store.get_candidate_embedding(candidate_id)
            job_data = vector_store.get_job_embedding(job_id)

            if (
                candidate_data
                and job_data
                and candidate_data.get("embedding")
                and job_data.get("embedding")
            ):
                return compute_cosine_similarity(
                    candidate_data["embedding"],
                    job_data["embedding"],
                )
        except Exception as exc:
            logger.warning("semantic_score_failed", error=str(exc))
        return 0.0

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _estimate_years(candidate: CandidateProfile) -> float:
        """Estimate total years of experience from experience entries."""
        total = 0.0
        for exp in candidate.experiences:
            start = exp.start_date or ""
            end = exp.end_date or ""

            start_year = None
            end_year = None

            # Extract 4-digit years
            start_match = re.search(r"(\d{4})", start)
            if start_match:
                start_year = int(start_match.group(1))
            end_match = re.search(r"(\d{4})", end)
            if end_match:
                end_year = int(end_match.group(1))

            if exp.is_current and start_year:
                from datetime import datetime
                end_year = datetime.now().year

            if start_year and end_year and end_year >= start_year:
                total += end_year - start_year
            elif start_year:
                total += 1  # minimum 1 year

        return total

    @staticmethod
    def _get_matched_skills(
        candidate: CandidateProfile, analysis: Any,
    ) -> list[str]:
        """Return list of required skill names that the candidate has."""
        candidate_skills_lower = MatchingService._candidate_terms(candidate)
        raw_text_lower = (candidate.raw_text or "").lower()
        matched = []
        for skill in (analysis.required_skills or []) + (analysis.preferred_skills or []):
            name = skill.get("name", "").lower()
            if any(name in cs or cs in name for cs in candidate_skills_lower):
                matched.append(skill.get("name", ""))
            elif raw_text_lower and name in raw_text_lower:
                matched.append(skill.get("name", ""))
        return matched

    @staticmethod
    def _candidate_terms(candidate: CandidateProfile) -> set[str]:
        terms = {s.skill_name.lower() for s in candidate.skills if s.skill_name}
        for project in candidate.projects or []:
            terms.update(MatchingService._split_terms(project.technologies or ""))
        for exp in candidate.experiences or []:
            terms.update(MatchingService._split_terms(exp.technologies or ""))
        return {term for term in terms if term}

    @staticmethod
    def _split_terms(value: str) -> set[str]:
        return {
            item.strip().lower()
            for item in re.split(r"[,;/|]", value)
            if item.strip()
        }

    @staticmethod
    def _requirement_names(analysis: Any) -> list[str]:
        names = []
        for skill in (analysis.required_skills or []) + (analysis.preferred_skills or []):
            name = (skill.get("name") or "").strip().lower()
            if name:
                names.append(name)
        return list(dict.fromkeys(names))

    @staticmethod
    def _term_matches_text(term: str, text: str) -> bool:
        return term in text or any(part and part in text for part in re.split(r"[\s/+-]+", term) if len(part) > 2)

    @staticmethod
    def _get_missing_skills(candidate: CandidateProfile, analysis: Any) -> list[str]:
        matched = {name.lower() for name in MatchingService._get_matched_skills(candidate, analysis)}
        return [
            skill.get("name", "")
            for skill in (analysis.required_skills or [])
            if skill.get("name") and skill.get("name", "").lower() not in matched
        ]

    @staticmethod
    def _build_strength_areas(
        skill_score: float,
        exp_score: float,
        project_score: float,
        edu_score: float,
        certification_score: float,
        achievement_score: float,
    ) -> list[str]:
        components = [
            ("Skills", skill_score),
            ("Experience", exp_score),
            ("Projects", project_score),
            ("Education", edu_score),
            ("Certifications", certification_score),
            ("Achievements", achievement_score),
        ]
        return [name for name, score in components if score >= 0.5]

    @staticmethod
    def _match_recommendation(score: float) -> str:
        if score >= 0.75:
            return "Strong match"
        if score >= 0.50:
            return "Consider"
        if score > 0:
            return "Low match with identifiable overlap"
        return "No measurable overlap"
