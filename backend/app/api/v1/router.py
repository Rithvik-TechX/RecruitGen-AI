"""
API v1 Router Aggregator.

All v1 sub-routers are included here.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_jobs,
    ai_resumes,
    ai_status,
    analytics,
    applications,
    auth,
    candidates,
    counts,
    evaluations,
    interviews,
    jobs,
    notifications,
    offers,
    organizations,
    pipeline,
    recommendations,
    reports,
    resumes,
    users,
)

api_v1_router = APIRouter()

# ── Authentication ──────────────────────────────────────────
api_v1_router.include_router(
    auth.router, prefix="/auth", tags=["Authentication"],
)

# ── Users ───────────────────────────────────────────────────
api_v1_router.include_router(
    users.router, prefix="/users", tags=["Users"],
)

# Organizations
api_v1_router.include_router(
    organizations.router, prefix="/organizations", tags=["Organizations"],
)

# ── Jobs ────────────────────────────────────────────────────
api_v1_router.include_router(
    jobs.router, prefix="/jobs", tags=["Jobs"],
)

# ── Applications ────────────────────────────────────────────
api_v1_router.include_router(
    applications.router, prefix="/applications", tags=["Applications"],
)
# Nested route: GET /jobs/{id}/applications
api_v1_router.include_router(
    applications.job_applications_router, prefix="/jobs", tags=["Jobs"],
)

# ── Resumes ─────────────────────────────────────────────────
api_v1_router.include_router(
    resumes.router, prefix="/resumes", tags=["Resumes"],
)

# ── AI Core: Resume Parsing ────────────────────────────────
api_v1_router.include_router(
    ai_resumes.router, prefix="/resumes", tags=["AI - Resume Intelligence"],
)

api_v1_router.include_router(
    ai_status.router, prefix="/ai", tags=["AI - Status"],
)

# ── AI Core: Candidates ────────────────────────────────────
api_v1_router.include_router(
    candidates.router, prefix="/candidates", tags=["AI - Candidates"],
)

# ── AI Core: JD Analysis, Matching, Ranking ────────────────
api_v1_router.include_router(
    ai_jobs.router, prefix="/jobs", tags=["AI - Job Intelligence"],
)

# ── AI Core: Full Pipeline ─────────────────────────────────
api_v1_router.include_router(
    pipeline.router, prefix="/pipeline", tags=["AI - Pipeline"],
)

# ── Interviews ─────────────────────────────────────────────
api_v1_router.include_router(
    interviews.router, tags=["Interviews"],
)

# ── Notifications ──────────────────────────────────────────
api_v1_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"],
)

# ── Analytics ──────────────────────────────────────────────
api_v1_router.include_router(
    analytics.router, prefix="/analytics", tags=["Analytics"],
)

# ── Reports ────────────────────────────────────────────────
api_v1_router.include_router(
    reports.router, prefix="/reports", tags=["Reports"],
)

# ── Skill Evaluations ─────────────────────────────────────
api_v1_router.include_router(
    evaluations.router, tags=["AI - Skill Evaluation"],
)

# ── Hiring Recommendations ─────────────────────────────────
api_v1_router.include_router(
    recommendations.router, tags=["AI - Hiring Recommendations"],
)

# ── Offer Letters ─────────────────────────────────────────
api_v1_router.include_router(
    offers.router, prefix="/offers", tags=["Offers"],
)

# ── Sidebar Counts ────────────────────────────────────────
api_v1_router.include_router(
    counts.router, prefix="/counts", tags=["Counts"],
)
