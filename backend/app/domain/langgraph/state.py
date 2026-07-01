"""
LangGraph Workflow State — shared state for the recruitment AI pipeline.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecruitmentState:
    """Shared state passed through the LangGraph workflow.

    Flow:
        Resume Upload → Resume Parser → Profile Builder
        → JD Analysis → Matching Engine → Ranking Engine
        → Skill Evaluation → Hiring Recommendation
    """

    # ── Input ───────────────────────────────────────────────
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None

    # ── Resume Parsing Output ───────────────────────────────
    raw_text: str = ""
    parsed_data: dict[str, Any] = field(default_factory=dict)

    # ── Candidate Profile ───────────────────────────────────
    candidate_id: uuid.UUID | None = None
    candidate_profile: dict[str, Any] = field(default_factory=dict)

    # ── JD Analysis ─────────────────────────────────────────
    job_analysis: dict[str, Any] = field(default_factory=dict)

    # ── Matching ────────────────────────────────────────────
    match_results: list[dict[str, Any]] = field(default_factory=list)

    # ── Ranking ─────────────────────────────────────────────
    ranking_results: list[dict[str, Any]] = field(default_factory=list)

    # ── Skill Evaluation ───────────────────────────────────
    evaluation_results: list[dict[str, Any]] = field(default_factory=list)

    # ── Hiring Recommendation ──────────────────────────────
    recommendation_results: list[dict[str, Any]] = field(default_factory=list)

    # ── Status ──────────────────────────────────────────────
    current_step: str = "init"
    errors: list[str] = field(default_factory=list)
    completed: bool = False
