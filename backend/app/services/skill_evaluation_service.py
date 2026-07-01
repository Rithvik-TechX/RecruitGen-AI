"""
Skill Evaluation Service — AI-powered technical skill assessment.

Uses Gemini to evaluate candidate skills against job requirements,
producing technical scores, competency breakdowns, and gap analysis.
"""

from __future__ import annotations

import json
import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_evaluation import EvaluationType, SkillEvaluation
from app.providers.gemini_provider import GeminiProvider, mark_ai_failure
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.skill_evaluation_repository import SkillEvaluationRepository

logger = structlog.get_logger(__name__)


class SkillEvaluationService:
    """Evaluates candidate skills using Gemini AI."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._eval_repo = SkillEvaluationRepository(session)
        self._candidate_repo = CandidateProfileRepository(session)
        self._job_analysis_repo = JobAnalysisRepository(session)
        self._gemini = GeminiProvider()

    async def evaluate_candidate(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> SkillEvaluation:
        """Run AI skill evaluation for a candidate-job pair."""
        # Check for existing evaluation
        existing = await self._eval_repo.get_by_candidate_and_job(
            candidate_id, job_id,
        )
        if existing:
            await self._session.delete(existing)
            await self._session.flush()

        # Load candidate profile
        candidate = await self._candidate_repo.get_by_id_with_details(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found",
            )

        # Load job analysis
        job_analysis = await self._job_analysis_repo.get_by_job_id(job_id)

        # Build context for Gemini
        candidate_skills = [
            {
                "name": s.skill_name,
                "level": s.proficiency_level,
                "years": s.years_of_experience,
                "category": s.category,
            }
            for s in candidate.skills
        ]
        candidate_experience = [
            {
                "company": e.company,
                "title": e.title,
                "description": e.description,
                "technologies": e.technologies,
            }
            for e in candidate.experiences
        ]
        candidate_projects = [
            {
                "name": p.project_name,
                "description": p.description,
                "technologies": p.technologies,
            }
            for p in candidate.projects
        ]
        candidate_certifications = [
            {
                "name": c.certification_name,
                "issuer": c.issuing_organization,
            }
            for c in candidate.certifications
        ]

        job_requirements = {}
        if job_analysis:
            job_requirements = {
                "required_skills": job_analysis.required_skills or [],
                "preferred_skills": job_analysis.preferred_skills or [],
                "education_requirements": job_analysis.education_requirements or {},
                "experience_requirements": job_analysis.experience_requirements or {},
            }

        prompt = f"""You are a technical recruiter AI. Evaluate the candidate's skills against the job requirements.

CANDIDATE SKILLS:
{json.dumps(candidate_skills, indent=2)}

CANDIDATE EXPERIENCE:
{json.dumps(candidate_experience, indent=2)}

CANDIDATE PROJECTS:
{json.dumps(candidate_projects, indent=2)}

CANDIDATE CERTIFICATIONS:
{json.dumps(candidate_certifications, indent=2)}

JOB REQUIREMENTS:
{json.dumps(job_requirements, indent=2)}

Respond with ONLY valid JSON (no markdown):
{{
    "technical_score": <float 0-100>,
    "competency_scores": {{
        "programming": <float 0-100>,
        "frameworks": <float 0-100>,
        "databases": <float 0-100>,
        "cloud_devops": <float 0-100>,
        "soft_skills": <float 0-100>,
        "domain_knowledge": <float 0-100>
    }},
    "skill_gaps": [
        {{"skill": "<name>", "importance": "critical|important|nice_to_have", "suggestion": "<learning path>"}}
    ],
    "strengths": ["<strength 1>", "<strength 2>"],
    "evaluation_summary": "<2-3 sentence overall assessment>"
}}"""

        try:
            response = await self._gemini.generate(prompt)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(cleaned)
        except Exception as exc:
            mark_ai_failure(exc, fallback_available=True)
            logger.exception("gemini_skill_evaluation_failed")
            # Deterministic fallback: compute score from available data
            fallback_score = self._compute_fallback_score(
                candidate_skills,
                candidate_experience,
                candidate_projects,
                candidate_certifications,
                job_requirements,
            )
            result = fallback_score

        if (
            float(result.get("technical_score") or 0) <= 0
            and (candidate_skills or candidate_experience or candidate_projects or candidate_certifications)
        ):
            result = self._compute_fallback_score(
                candidate_skills,
                candidate_experience,
                candidate_projects,
                candidate_certifications,
                job_requirements,
            )

        evaluation = SkillEvaluation(
            candidate_id=candidate_id,
            job_id=job_id,
            technical_score=float(result.get("technical_score", 0)),
            competency_scores=result.get("competency_scores"),
            skill_gaps=result.get("skill_gaps"),
            strengths=result.get("strengths"),
            evaluation_summary=result.get("evaluation_summary"),
            evaluated_by=EvaluationType.AI,
        )
        evaluation = await self._eval_repo.create(evaluation)
        await self._session.commit()

        logger.info(
            "skill_evaluation_completed",
            candidate_id=str(candidate_id),
            job_id=str(job_id),
            score=evaluation.technical_score,
        )
        return evaluation

    async def get_evaluation(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> SkillEvaluation:
        """Get existing evaluation for a candidate-job pair."""
        evaluation = await self._eval_repo.get_by_candidate_and_job(
            candidate_id, job_id,
        )
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill evaluation not found",
            )
        return evaluation

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> tuple[list[SkillEvaluation], int]:
        """List evaluations for a job."""
        evaluations = await self._eval_repo.list_by_job(
            job_id, skip=skip, limit=limit,
        )
        total = await self._eval_repo.count_by_job(job_id)
        return evaluations, total

    @staticmethod
    def _compute_fallback_score(
        candidate_skills: list[dict],
        candidate_experience: list[dict],
        candidate_projects: list[dict],
        candidate_certifications: list[dict],
        job_requirements: dict,
    ) -> dict:
        """Deterministic evaluation when Gemini is unavailable."""
        required = job_requirements.get("required_skills", [])
        preferred = job_requirements.get("preferred_skills", [])
        candidate_names = {s["name"].lower() for s in candidate_skills if s.get("name")}
        project_text = " ".join(
            " ".join(str(value or "") for value in project.values())
            for project in candidate_projects
        ).lower()
        cert_text = " ".join(
            " ".join(str(value or "") for value in cert.values())
            for cert in candidate_certifications
        ).lower()

        # Skill overlap score
        required_names = {s.get("name", "").lower() for s in required if s.get("name")}
        preferred_names = {s.get("name", "").lower() for s in preferred if s.get("name")}

        def matches(name: str) -> bool:
            return (
                any(name in cn or cn in name for cn in candidate_names)
                or name in project_text
                or name in cert_text
            )

        req_matched = sum(1 for rn in required_names if matches(rn))
        pref_matched = sum(1 for pn in preferred_names if matches(pn))

        req_score = (req_matched / len(required_names) * 100) if required_names else 50.0
        pref_score = (pref_matched / len(preferred_names) * 100) if preferred_names else 50.0

        # Evidence breadth scores
        exp_score = min(100.0, len(candidate_experience) * 25.0)
        project_score = min(100.0, len(candidate_projects) * 25.0)
        cert_score = min(100.0, len(candidate_certifications) * 30.0)

        # Overall technical score (weighted)
        technical_score = round(
            0.45 * req_score
            + 0.20 * pref_score
            + 0.15 * project_score
            + 0.15 * exp_score
            + 0.05 * cert_score,
            1,
        )
        if candidate_skills or candidate_experience or candidate_projects or candidate_certifications:
            technical_score = max(10.0, min(95.0, technical_score))

        # Build strengths
        strengths = []
        if req_matched > 0:
            matched_list = [
                rn for rn in required_names
                if any(rn in cn or cn in rn for cn in candidate_names)
            ]
            strengths.append(f"Matches {req_matched}/{len(required_names)} required skills: {', '.join(list(matched_list)[:5])}")
        if candidate_experience:
            strengths.append(f"Has {len(candidate_experience)} relevant experience entries")
        if candidate_projects:
            strengths.append(f"Includes {len(candidate_projects)} project entries")
        if candidate_certifications:
            strengths.append(f"Includes {len(candidate_certifications)} certifications")
        if len(candidate_skills) >= 10:
            strengths.append(f"Strong technical breadth with {len(candidate_skills)} documented skills")

        # Build skill gaps
        missing_required = [
            rn for rn in required_names
            if not any(rn in cn or cn in rn for cn in candidate_names)
        ]
        skill_gaps = [
            {"skill": name.title(), "importance": "critical", "suggestion": f"Develop proficiency in {name.title()}"}
            for name in list(missing_required)[:5]
        ]

        return {
            "technical_score": technical_score,
            "competency_scores": {
                "programming": req_score,
                "frameworks": pref_score,
                "databases": 50.0,
                "cloud_devops": 50.0,
                "soft_skills": 60.0,
                "domain_knowledge": max(exp_score, project_score),
            },
            "skill_gaps": skill_gaps,
            "strengths": strengths or ["Candidate profile available for review"],
            "evaluation_summary": (
                f"Deterministic evaluation: candidate matches {req_matched} of "
                f"{len(required_names)} required skills with {len(candidate_experience)} "
                f"experience entries, {len(candidate_projects)} projects, and "
                f"{len(candidate_certifications)} certifications. Overall technical score: {technical_score}/100."
            ),
        }
