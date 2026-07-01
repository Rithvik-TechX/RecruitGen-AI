"""
Hiring Recommendation Service — ATS-score-driven hire/consider/reject decisions.

Uses match scores, skill evaluations, and Gemini AI analysis to produce
an ATS score (0-100) and map it to a hiring decision:
  80+  → Hire
  60-79 → Consider
  <60  → Reject
"""

from __future__ import annotations

import json
import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hiring_recommendation import HiringDecision, HiringRecommendation
from app.providers.gemini_provider import GeminiProvider, mark_ai_failure
from app.repositories.candidate_match_repository import CandidateMatchRepository
from app.repositories.candidate_repository import CandidateProfileRepository
from app.repositories.hiring_recommendation_repository import (
    HiringRecommendationRepository,
)
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.skill_evaluation_repository import SkillEvaluationRepository

logger = structlog.get_logger(__name__)


def _ats_decision(score: float) -> HiringDecision:
    """Map an ATS score (0-100) to a hiring decision."""
    if score >= 80:
        return HiringDecision.HIRE
    if score >= 60:
        return HiringDecision.CONSIDER
    return HiringDecision.REJECT


def _compute_ats_score(
    match: object | None,
    evaluation: object | None,
) -> float:
    """Compute an ATS score (0-100) from match and evaluation data.

    Weights:
      - Overall match score:  40%
      - Skill match score:    20%
      - Experience match:     15%
      - Education match:      10%
      - Technical eval score: 15%

    Match scores are stored as 0-1 fractions and must be scaled to 0-100.
    Technical eval score is already 0-100.
    """
    components: list[tuple[float, float]] = []  # (weight, score_0_to_100)

    if match:
        # Match scores are 0-1 fractions → multiply by 100
        overall = (getattr(match, "overall_match_score", None) or 0) * 100
        skill = (getattr(match, "skill_match_score", None) or 0) * 100
        experience = (getattr(match, "experience_match_score", None) or 0) * 100
        education = (getattr(match, "education_match_score", None) or 0) * 100

        components.append((0.40, float(overall)))
        components.append((0.20, float(skill)))
        components.append((0.15, float(experience)))
        components.append((0.10, float(education)))

    if evaluation:
        # Technical score is already 0-100
        tech_score = getattr(evaluation, "technical_score", None) or 0
        components.append((0.15, float(tech_score)))

    if not components:
        return 0.0

    # Normalize weights if not all components are present
    total_weight = sum(w for w, _ in components)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(w * s for w, s in components)
    score = round(weighted_sum / total_weight, 1)
    return max(1.0, score) if score > 0 else 0.0


class HiringRecommendationService:
    """Generates AI-powered hiring recommendations with ATS scoring."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._rec_repo = HiringRecommendationRepository(session)
        self._candidate_repo = CandidateProfileRepository(session)
        self._match_repo = CandidateMatchRepository(session)
        self._eval_repo = SkillEvaluationRepository(session)
        self._job_analysis_repo = JobAnalysisRepository(session)
        self._gemini = GeminiProvider()

    async def recommend(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> HiringRecommendation:
        """Generate a hiring recommendation for a candidate-job pair."""
        # Remove existing recommendation
        existing = await self._rec_repo.get_by_candidate_and_job(
            candidate_id, job_id,
        )
        if existing:
            await self._session.delete(existing)
            await self._session.flush()

        # Load all data
        candidate = await self._candidate_repo.get_by_id_with_details(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found",
            )

        match = await self._match_repo.get_by_candidate_and_job(candidate_id, job_id)
        evaluation = await self._eval_repo.get_by_candidate_and_job(
            candidate_id, job_id,
        )
        job_analysis = await self._job_analysis_repo.get_by_job_id(job_id)

        # Compute ATS score from available data
        ats_score = _compute_ats_score(match, evaluation)
        if ats_score == 0.0 and (
            candidate.skills
            or candidate.experiences
            or candidate.projects
            or candidate.certifications
        ):
            evidence_score = min(
                45.0,
                len(candidate.skills) * 1.5
                + len(candidate.projects) * 5.0
                + len(candidate.experiences) * 6.0
                + len(candidate.certifications) * 4.0,
            )
            ats_score = round(max(10.0, evidence_score), 1)

        # Build context for Gemini
        context = {
            "candidate_name": candidate.full_name,
            "candidate_summary": candidate.summary or "",
            "skills": [s.skill_name for s in candidate.skills],
            "experience_count": len(candidate.experiences),
            "project_count": len(candidate.projects),
            "certification_count": len(candidate.certifications),
            "education": [
                {"degree": e.degree, "institution": e.institution}
                for e in candidate.education
            ],
            "ats_score": ats_score,
            "match_scores": {},
            "skill_evaluation": {},
            "job_requirements": {},
        }

        if match:
            context["match_scores"] = {
                "overall": match.overall_match_score,
                "skill": match.skill_match_score,
                "experience": match.experience_match_score,
                "education": match.education_match_score,
                "semantic": match.semantic_similarity_score,
            }

        if evaluation:
            context["skill_evaluation"] = {
                "technical_score": evaluation.technical_score,
                "competency_scores": evaluation.competency_scores or {},
                "skill_gaps": evaluation.skill_gaps or [],
                "strengths": evaluation.strengths or [],
            }

        if job_analysis:
            context["job_requirements"] = {
                "required_skills": job_analysis.required_skills or [],
                "experience": job_analysis.experience_requirements or {},
            }

        prompt = f"""You are a senior HR AI advisor. Based on the candidate's data and ATS score, produce a detailed hiring recommendation.

CANDIDATE & EVALUATION DATA:
{json.dumps(context, indent=2)}

ATS SCORING RULES:
- ATS Score >= 80: Decision MUST be "hire"
- ATS Score 60-79: Decision MUST be "consider"
- ATS Score < 60: Decision MUST be "reject"

The candidate's computed ATS score is {ats_score}.

Respond with ONLY valid JSON (no markdown):
{{
    "risk_assessment": "<assessment of hiring risks>",
    "strengths": [
        {{"area": "<area>", "detail": "<explanation>"}}
    ],
    "weaknesses": [
        {{"area": "<area>", "detail": "<explanation>"}}
    ],
    "reasoning": "<detailed reasoning for the decision based on scores and qualifications>",
    "summary": "<one-sentence recommendation>"
}}"""

        # Determine decision from ATS score (score-driven, not AI-driven)
        decision = _ats_decision(ats_score)
        confidence = max(0.01, ats_score / 100.0)  # Normalize to 0-1 for storage

        try:
            response = await self._gemini.generate(prompt)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(cleaned)
        except Exception as exc:
            mark_ai_failure(exc, fallback_available=True)
            logger.exception("gemini_hiring_recommendation_failed")
            # Build a meaningful fallback from real data
            strengths = []
            weaknesses = []

            if match:
                overall_pct = round((match.overall_match_score or 0) * 100, 1)
                skill_pct = round((match.skill_match_score or 0) * 100, 1)
                exp_pct = round((match.experience_match_score or 0) * 100, 1)
                edu_pct = round((match.education_match_score or 0) * 100, 1)

                if overall_pct >= 70:
                    strengths.append({"area": "Overall Match", "detail": f"Strong overall match score of {overall_pct}%"})
                elif overall_pct > 0:
                    weaknesses.append({"area": "Overall Match", "detail": f"Match score of {overall_pct}% needs improvement"})

                if skill_pct >= 70:
                    strengths.append({"area": "Skills", "detail": f"Good skill alignment at {skill_pct}%"})
                elif skill_pct > 0:
                    weaknesses.append({"area": "Skills", "detail": f"Skill match at {skill_pct}% — gaps may exist"})

            if evaluation:
                if evaluation.technical_score and evaluation.technical_score >= 70:
                    strengths.append({"area": "Technical", "detail": f"Technical evaluation score: {evaluation.technical_score}%"})
                elif evaluation.technical_score:
                    weaknesses.append({"area": "Technical", "detail": f"Technical score of {evaluation.technical_score}% needs improvement"})

                if evaluation.strengths:
                    for s in evaluation.strengths[:3]:
                        if isinstance(s, str):
                            strengths.append({"area": "Evaluation", "detail": s})
                        elif isinstance(s, dict):
                            strengths.append(s)

            if not strengths and not weaknesses:
                if ats_score >= 60:
                    strengths.append({"area": "Profile", "detail": f"ATS score of {ats_score}% based on available match data"})
                else:
                    weaknesses.append({"area": "Profile", "detail": f"ATS score of {ats_score}% indicates gaps in match criteria"})

            decision_labels = {HiringDecision.HIRE: "hire", HiringDecision.CONSIDER: "further review", HiringDecision.REJECT: "rejection"}
            result = {
                "risk_assessment": f"ATS score is {ats_score}%. {'Low risk — strong candidate.' if ats_score >= 80 else 'Medium risk — review recommended.' if ats_score >= 60 else 'Higher risk — significant gaps identified.'}",
                "strengths": strengths,
                "weaknesses": weaknesses,
                "reasoning": f"Based on ATS scoring criteria, the candidate has an overall score of {ats_score}% which maps to {decision_labels.get(decision, 'review')}. "
                    + (f"Overall match: {overall_pct}%, Skill match: {skill_pct}%, Experience: {exp_pct}%, Education: {edu_pct}%." if match else "No detailed match data available.")
                    + (f" Technical evaluation: {evaluation.technical_score}%." if evaluation and evaluation.technical_score else ""),
                "summary": f"ATS Score: {ats_score}% — Recommended for {decision_labels.get(decision, 'review')}.",
            }

        recommendation = HiringRecommendation(
            candidate_id=candidate_id,
            job_id=job_id,
            decision=decision,
            confidence_score=confidence,
            risk_assessment=result.get("risk_assessment"),
            strengths=result.get("strengths"),
            weaknesses=result.get("weaknesses"),
            reasoning=result.get("reasoning"),
            summary=result.get("summary"),
        )
        recommendation = await self._rec_repo.create(recommendation)
        await self._session.commit()

        logger.info(
            "hiring_recommendation_generated",
            candidate_id=str(candidate_id),
            job_id=str(job_id),
            decision=decision.value,
            ats_score=ats_score,
            confidence=recommendation.confidence_score,
        )
        return recommendation

    async def get_recommendation(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID,
    ) -> HiringRecommendation:
        """Get an existing recommendation."""
        rec = await self._rec_repo.get_by_candidate_and_job(candidate_id, job_id)
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hiring recommendation not found",
            )
        return rec

    async def list_by_job(
        self, job_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> tuple[list[HiringRecommendation], int]:
        """List recommendations for a job."""
        recs = await self._rec_repo.list_by_job(job_id, skip=skip, limit=limit)
        total = len(recs)
        return recs, total
