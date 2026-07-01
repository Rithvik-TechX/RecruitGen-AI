"""
LangGraph Workflow Nodes — individual processing steps.

Each node receives the current state, performs its task, and returns
the updated state.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.langgraph.state import RecruitmentState
from app.services.resume_intelligence_service import ResumeIntelligenceService
from app.services.jd_analysis_service import JDAnalysisService
from app.services.matching_service import MatchingService
from app.services.ranking_service import RankingService
from app.services.skill_evaluation_service import SkillEvaluationService
from app.services.hiring_recommendation_service import HiringRecommendationService

logger = structlog.get_logger(__name__)


# ── Node: Resume Parser ────────────────────────────────────


async def resume_parser_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Extract text from resume and parse with AI."""
    state.current_step = "resume_parsing"
    logger.info("node_executing", node="resume_parser", resume_id=str(state.resume_id))

    try:
        service = ResumeIntelligenceService(session)
        profile = await service.parse_resume(state.resume_id)

        state.candidate_id = profile.id
        state.candidate_profile = {
            "id": str(profile.id),
            "full_name": profile.full_name,
            "email": profile.email,
            "skills_count": len(profile.skills),
            "experience_count": len(profile.experiences),
            "education_count": len(profile.education),
            "projects_count": len(profile.projects),
            "certifications_count": len(profile.certifications),
        }
        state.raw_text = profile.raw_text or ""
        logger.info("node_completed", node="resume_parser", candidate_id=str(profile.id))

    except Exception as exc:
        error_msg = f"Resume parsing failed: {exc}"
        state.errors.append(error_msg)
        logger.error("node_failed", node="resume_parser", error=str(exc))

    return state


# ── Node: Candidate Profile Builder ────────────────────────


async def profile_builder_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Verify candidate profile is complete."""
    state.current_step = "profile_building"
    logger.info("node_executing", node="profile_builder")

    if not state.candidate_id:
        state.errors.append("No candidate profile available — resume parsing may have failed.")
        return state

    try:
        service = ResumeIntelligenceService(session)
        profile = await service.get_candidate(state.candidate_id)

        state.candidate_profile = {
            "id": str(profile.id),
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "skills": [s.skill_name for s in profile.skills],
            "experience": [
                {"company": e.company, "title": e.title}
                for e in profile.experiences
            ],
            "education": [
                {"institution": ed.institution, "degree": ed.degree}
                for ed in profile.education
            ],
            "projects": [p.project_name for p in profile.projects],
            "certifications": [c.certification_name for c in profile.certifications],
            "parsing_status": profile.parsing_status.value,
        }
        logger.info("node_completed", node="profile_builder")

    except Exception as exc:
        state.errors.append(f"Profile building failed: {exc}")
        logger.error("node_failed", node="profile_builder", error=str(exc))

    return state


# ── Node: JD Analysis ──────────────────────────────────────


async def jd_analysis_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Analyse job description with AI."""
    state.current_step = "jd_analysis"
    logger.info("node_executing", node="jd_analysis", job_id=str(state.job_id))

    if not state.job_id:
        state.errors.append("No job_id provided for JD analysis.")
        return state

    try:
        service = JDAnalysisService(session)
        analysis = await service.analyze_job(state.job_id)

        state.job_analysis = {
            "job_id": str(analysis.job_id),
            "required_skills": analysis.required_skills or [],
            "preferred_skills": analysis.preferred_skills or [],
            "education_requirements": analysis.education_requirements or {},
            "experience_requirements": analysis.experience_requirements or {},
            "keywords": analysis.keywords or [],
            "status": analysis.analysis_status.value,
        }
        logger.info("node_completed", node="jd_analysis")

    except Exception as exc:
        state.errors.append(f"JD analysis failed: {exc}")
        logger.error("node_failed", node="jd_analysis", error=str(exc))

    return state


# ── Node: Matching Engine ──────────────────────────────────


async def matching_engine_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Match candidates against the job."""
    state.current_step = "matching"
    logger.info("node_executing", node="matching_engine", job_id=str(state.job_id))

    if not state.job_id:
        state.errors.append("No job_id provided for matching.")
        return state

    try:
        service = MatchingService(session)
        matches = await service.match_candidates_to_job(state.job_id)

        state.match_results = [
            {
                "candidate_id": str(m.candidate_id),
                "candidate_name": m.candidate.full_name if m.candidate else "",
                "skill_match": m.skill_match_score,
                "experience_match": m.experience_match_score,
                "education_match": m.education_match_score,
                "semantic_similarity": m.semantic_similarity_score,
                "overall": m.overall_match_score,
            }
            for m in matches
        ]
        logger.info(
            "node_completed",
            node="matching_engine",
            matches_count=len(matches),
        )

    except Exception as exc:
        state.errors.append(f"Matching failed: {exc}")
        logger.error("node_failed", node="matching_engine", error=str(exc))

    return state


# ── Node: Ranking Engine ───────────────────────────────────


async def ranking_engine_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Rank candidates for the job."""
    state.current_step = "ranking"
    logger.info("node_executing", node="ranking_engine", job_id=str(state.job_id))

    if not state.job_id:
        state.errors.append("No job_id provided for ranking.")
        return state

    try:
        service = RankingService(session)
        rankings = await service.rank_candidates(state.job_id)

        state.ranking_results = [
            {
                "rank": r.rank_position,
                "candidate_id": str(r.candidate_id),
                "candidate_name": r.candidate.full_name if r.candidate else "",
                "final_score": r.final_score,
                "skill_score": r.skill_score,
                "experience_score": r.experience_score,
                "education_score": r.education_score,
                "project_score": r.project_score,
                "semantic_score": r.semantic_score,
            }
            for r in rankings
        ]
        logger.info(
            "node_completed",
            node="ranking_engine",
            ranked_count=len(rankings),
        )

    except Exception as exc:
        state.errors.append(f"Ranking failed: {exc}")
        logger.error("node_failed", node="ranking_engine", error=str(exc))

    return state


# ── Node: Skill Evaluation ─────────────────────────────────


async def skill_evaluation_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Evaluate each ranked candidate's skills with AI."""
    state.current_step = "skill_evaluation"
    logger.info("node_executing", node="skill_evaluation", job_id=str(state.job_id))

    if not state.job_id or not state.ranking_results:
        state.errors.append("No ranking results available for skill evaluation.")
        return state

    try:
        import uuid

        service = SkillEvaluationService(session)
        results = []
        for ranked in state.ranking_results[:10]:  # Evaluate top 10
            candidate_id = uuid.UUID(ranked["candidate_id"])
            try:
                evaluation = await service.evaluate_candidate(candidate_id, state.job_id)
                results.append({
                    "candidate_id": str(candidate_id),
                    "candidate_name": ranked.get("candidate_name", ""),
                    "technical_score": evaluation.technical_score,
                    "competency_scores": evaluation.competency_scores or {},
                    "skill_gaps": evaluation.skill_gaps or [],
                    "strengths": evaluation.strengths or [],
                    "summary": evaluation.evaluation_summary or "",
                })
            except Exception as inner_exc:
                logger.warning(
                    "skill_evaluation_candidate_failed",
                    candidate_id=str(candidate_id),
                    error=str(inner_exc),
                )

        state.evaluation_results = results
        logger.info(
            "node_completed",
            node="skill_evaluation",
            evaluated_count=len(results),
        )

    except Exception as exc:
        state.errors.append(f"Skill evaluation failed: {exc}")
        logger.error("node_failed", node="skill_evaluation", error=str(exc))

    return state


# ── Node: Hiring Recommendation ────────────────────────────


async def hiring_recommendation_node(
    state: RecruitmentState, session: AsyncSession,
) -> RecruitmentState:
    """Generate hiring recommendations for evaluated candidates."""
    state.current_step = "hiring_recommendation"
    logger.info("node_executing", node="hiring_recommendation", job_id=str(state.job_id))

    if not state.job_id or not state.evaluation_results:
        state.errors.append("No evaluation results available for recommendations.")
        state.completed = True
        return state

    try:
        import uuid

        service = HiringRecommendationService(session)
        results = []
        for evaluated in state.evaluation_results:
            candidate_id = uuid.UUID(evaluated["candidate_id"])
            try:
                rec = await service.recommend(candidate_id, state.job_id)
                results.append({
                    "candidate_id": str(candidate_id),
                    "candidate_name": evaluated.get("candidate_name", ""),
                    "decision": rec.decision.value,
                    "confidence_score": rec.confidence_score,
                    "risk_assessment": rec.risk_assessment or "",
                    "summary": rec.summary or "",
                })
            except Exception as inner_exc:
                logger.warning(
                    "hiring_recommendation_candidate_failed",
                    candidate_id=str(candidate_id),
                    error=str(inner_exc),
                )

        state.recommendation_results = results
        state.completed = True
        logger.info(
            "node_completed",
            node="hiring_recommendation",
            recommendation_count=len(results),
        )

    except Exception as exc:
        state.errors.append(f"Hiring recommendation failed: {exc}")
        logger.error("node_failed", node="hiring_recommendation", error=str(exc))
        state.completed = True

    return state
