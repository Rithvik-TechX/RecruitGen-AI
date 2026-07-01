"""
LangGraph Workflow Graph — orchestrates the full recruitment AI pipeline.

Pipeline:
    Resume Upload → Resume Parser → Profile Builder
    → JD Analysis → Matching Engine → Ranking Engine
    → Skill Evaluation → Hiring Recommendation
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.langgraph.state import RecruitmentState
from app.domain.langgraph.nodes import (
    hiring_recommendation_node,
    jd_analysis_node,
    matching_engine_node,
    profile_builder_node,
    ranking_engine_node,
    resume_parser_node,
    skill_evaluation_node,
)

logger = structlog.get_logger(__name__)


def _should_continue_after_parse(state: RecruitmentState) -> str:
    """Decide next step after resume parsing."""
    if state.errors:
        return "end"
    return "profile_builder"


def _should_continue_after_profile(state: RecruitmentState) -> str:
    """Decide next step after profile building."""
    if state.errors:
        return "end"
    if state.job_id:
        return "jd_analysis"
    return "end"  # No job specified — stop after profile


def _should_continue_after_analysis(state: RecruitmentState) -> str:
    """Decide next step after JD analysis."""
    if state.errors:
        return "end"
    return "matching_engine"


def _should_continue_after_matching(state: RecruitmentState) -> str:
    """Decide next step after matching."""
    if state.errors:
        return "end"
    return "ranking_engine"


def _should_continue_after_ranking(state: RecruitmentState) -> str:
    """Decide next step after ranking."""
    if state.errors:
        return "end"
    return "skill_evaluation"


def _should_continue_after_evaluation(state: RecruitmentState) -> str:
    """Decide next step after skill evaluation."""
    if state.errors:
        return "end"
    return "hiring_recommendation"


def build_recruitment_graph() -> StateGraph:
    """Build and return the LangGraph StateGraph for the recruitment pipeline.

    The graph is built once and can be invoked multiple times with
    different states.
    """
    graph = StateGraph(RecruitmentState)

    # ── Add nodes (placeholders — actual execution is async) ──
    graph.add_node("resume_parser", lambda state: state)
    graph.add_node("profile_builder", lambda state: state)
    graph.add_node("jd_analysis", lambda state: state)
    graph.add_node("matching_engine", lambda state: state)
    graph.add_node("ranking_engine", lambda state: state)
    graph.add_node("skill_evaluation", lambda state: state)
    graph.add_node("hiring_recommendation", lambda state: state)

    # ── Set entry point ─────────────────────────────────────
    graph.set_entry_point("resume_parser")

    # ── Add edges with conditional routing ──────────────────
    graph.add_conditional_edges(
        "resume_parser",
        _should_continue_after_parse,
        {"profile_builder": "profile_builder", "end": END},
    )
    graph.add_conditional_edges(
        "profile_builder",
        _should_continue_after_profile,
        {"jd_analysis": "jd_analysis", "end": END},
    )
    graph.add_conditional_edges(
        "jd_analysis",
        _should_continue_after_analysis,
        {"matching_engine": "matching_engine", "end": END},
    )
    graph.add_conditional_edges(
        "matching_engine",
        _should_continue_after_matching,
        {"ranking_engine": "ranking_engine", "end": END},
    )
    graph.add_conditional_edges(
        "ranking_engine",
        _should_continue_after_ranking,
        {"skill_evaluation": "skill_evaluation", "end": END},
    )
    graph.add_conditional_edges(
        "skill_evaluation",
        _should_continue_after_evaluation,
        {"hiring_recommendation": "hiring_recommendation", "end": END},
    )
    graph.add_edge("hiring_recommendation", END)

    return graph


async def run_recruitment_pipeline(
    session: AsyncSession,
    resume_id: uuid.UUID,
    job_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Run the full recruitment AI pipeline.

    This is the high-level orchestrator that runs each node in sequence,
    passing the database session to each node for DB access.

    Args:
        session: Async database session.
        resume_id: UUID of the uploaded resume to process.
        job_id: Optional UUID of the job to match/rank against.

    Returns:
        Final state dictionary with all results.
    """
    state = RecruitmentState(
        resume_id=resume_id,
        job_id=job_id,
    )

    logger.info(
        "pipeline_starting",
        resume_id=str(resume_id),
        job_id=str(job_id) if job_id else None,
    )

    # Execute nodes in sequence
    nodes = [
        ("resume_parser", resume_parser_node),
        ("profile_builder", profile_builder_node),
    ]

    if job_id:
        nodes.extend([
            ("jd_analysis", jd_analysis_node),
            ("matching_engine", matching_engine_node),
            ("ranking_engine", ranking_engine_node),
            ("skill_evaluation", skill_evaluation_node),
            ("hiring_recommendation", hiring_recommendation_node),
        ])

    for node_name, node_fn in nodes:
        if state.errors:
            logger.warning(
                "pipeline_stopping_on_error",
                step=node_name,
                errors=state.errors,
            )
            break
        state = await node_fn(state, session)

    state.current_step = "completed" if not state.errors else "failed"

    logger.info(
        "pipeline_finished",
        completed=state.completed,
        errors=state.errors,
        final_step=state.current_step,
    )

    return {
        "resume_id": str(state.resume_id) if state.resume_id else None,
        "job_id": str(state.job_id) if state.job_id else None,
        "candidate_id": str(state.candidate_id) if state.candidate_id else None,
        "candidate_profile": state.candidate_profile,
        "job_analysis": state.job_analysis,
        "match_results": state.match_results,
        "ranking_results": state.ranking_results,
        "evaluation_results": state.evaluation_results,
        "recommendation_results": state.recommendation_results,
        "current_step": state.current_step,
        "errors": state.errors,
        "completed": state.completed,
    }
