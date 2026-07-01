"""
Analytics Service — dashboard stats, hiring funnels, and pipeline metrics.

Uses raw SQLAlchemy queries for aggregation across multiple tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.candidate_match import CandidateMatch
from app.models.candidate_ranking import CandidateRanking
from app.models.interview_schedule import InterviewSchedule, InterviewStatus
from app.models.job import Job, JobStatus
from app.models.resume import Resume

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """Recruitment analytics and dashboard metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_dashboard_stats(
        self, organization_id: uuid.UUID | None = None,
    ) -> dict:
        """Compute top-level dashboard statistics."""
        job_filter = [Job.organization_id == organization_id] if organization_id else []
        # Total jobs
        total_jobs = (
            await self._session.execute(
                select(func.count()).select_from(Job).where(*job_filter),
            )
        ).scalar_one()

        # Total candidates who applied to this organization's jobs
        candidate_stmt = (
            select(func.count(func.distinct(Application.candidate_id)))
            .select_from(Application)
            .join(Job, Application.job_id == Job.id)
            .where(*job_filter)
        )
        total_candidates = (
            await self._session.execute(candidate_stmt)
        ).scalar_one()

        # Total applications
        application_base = (
            select(func.count())
            .select_from(Application)
            .join(Job, Application.job_id == Job.id)
            .where(*job_filter)
        )
        total_applications = (
            await self._session.execute(application_base)
        ).scalar_one()

        # Shortlisted or later in the application workflow
        shortlisted = (
            await self._session.execute(
                select(func.count(func.distinct(Application.candidate_id)))
                .select_from(Application)
                .join(Job, Application.job_id == Job.id)
                .where(
                    *job_filter,
                    Application.status.in_(
                        (
                            ApplicationStatus.SHORTLISTED,
                            ApplicationStatus.INTERVIEW_SCHEDULED,
                            ApplicationStatus.INTERVIEW_COMPLETED,
                            ApplicationStatus.SELECTED,
                        )
                    ),
                ),
            )
        ).scalar_one()

        # Rejected
        rejected = (
            await self._session.execute(
                select(func.count())
                .select_from(Application)
                .join(Job, Application.job_id == Job.id)
                .where(*job_filter, Application.status == ApplicationStatus.REJECTED),
            )
        ).scalar_one()

        # Interviews scheduled
        interviews_scheduled = (
            await self._session.execute(
                select(func.count())
                .select_from(InterviewSchedule)
                .join(Job, InterviewSchedule.job_id == Job.id)
                .where(*job_filter, InterviewSchedule.status == InterviewStatus.SCHEDULED),
            )
        ).scalar_one()

        # Hiring rate
        accepted = (
            await self._session.execute(
                select(func.count())
                .select_from(Application)
                .join(Job, Application.job_id == Job.id)
                .where(*job_filter, Application.status == ApplicationStatus.SELECTED),
            )
        ).scalar_one()

        hiring_rate = (accepted / total_applications * 100) if total_applications > 0 else 0.0

        return {
            "total_jobs": total_jobs,
            "total_candidates": total_candidates,
            "total_applications": total_applications,
            "shortlisted": shortlisted,
            "rejected": rejected,
            "interviews_scheduled": interviews_scheduled,
            "hiring_rate": round(hiring_rate, 2),
        }

    async def get_hiring_funnel(self, job_id: uuid.UUID) -> dict:
        """Get hiring funnel stages for a specific job."""
        # Get job title
        job = await self._session.get(Job, job_id)
        job_title = job.title if job else "Unknown"

        # Applied
        applied = (
            await self._session.execute(
                select(func.count())
                .select_from(Application)
                .where(Application.job_id == job_id),
            )
        ).scalar_one()

        # Screened (have candidate profiles)
        screened = (
            await self._session.execute(
                select(func.count(func.distinct(CandidateMatch.candidate_id)))
                .select_from(CandidateMatch)
                .where(CandidateMatch.job_id == job_id),
            )
        ).scalar_one()

        # Matched (match score > 50%)
        matched = (
            await self._session.execute(
                select(func.count())
                .select_from(CandidateMatch)
                .where(
                    CandidateMatch.job_id == job_id,
                    CandidateMatch.overall_match_score >= 50.0,
                ),
            )
        ).scalar_one()

        # Interviewed
        interviewed = (
            await self._session.execute(
                select(func.count())
                .select_from(InterviewSchedule)
                .where(InterviewSchedule.job_id == job_id),
            )
        ).scalar_one()

        # Offered
        offered = (
            await self._session.execute(
                select(func.count())
                .select_from(Application)
                .where(
                    Application.job_id == job_id,
                    Application.status == ApplicationStatus.SELECTED,
                ),
            )
        ).scalar_one()

        stages_raw = [
            ("Applied", applied),
            ("Screened", screened),
            ("Matched", matched),
            ("Interviewed", interviewed),
            ("Offered", offered),
        ]

        stages = []
        for name, count in stages_raw:
            pct = (count / applied * 100) if applied > 0 else 0.0
            stages.append({"stage": name, "count": count, "percentage": round(pct, 1)})

        return {"job_id": str(job_id), "job_title": job_title, "stages": stages}

    async def get_skill_distribution(
        self, organization_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Get top skills for candidates who applied to the organization."""
        latest_profiles = (
            select(
                Resume.candidate_id.label("candidate_user_id"),
                CandidateProfile.id.label("profile_id"),
            )
            .join(CandidateProfile, CandidateProfile.resume_id == Resume.id)
            .order_by(Resume.candidate_id, CandidateProfile.updated_at.desc())
            .distinct(Resume.candidate_id)
            .subquery()
        )
        stmt = (
            select(
                CandidateSkill.skill_name,
                func.count(func.distinct(CandidateSkill.id)).label("cnt"),
            )
            .join(
                latest_profiles,
                CandidateSkill.candidate_id == latest_profiles.c.profile_id,
            )
            .join(
                Application,
                Application.candidate_id == latest_profiles.c.candidate_user_id,
            )
            .join(Job, Application.job_id == Job.id)
            .where(
                *(
                    [Job.organization_id == organization_id]
                    if organization_id else []
                )
            )
            .group_by(CandidateSkill.skill_name)
            .order_by(func.count(func.distinct(CandidateSkill.id)).desc())
            .limit(20)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        total = sum(r.cnt for r in rows) if rows else 1
        return [
            {
                "skill_name": r.skill_name,
                "count": r.cnt,
                "percentage": round(r.cnt / total * 100, 1),
            }
            for r in rows
        ]

    async def get_pipeline_metrics(
        self, organization_id: uuid.UUID | None = None,
    ) -> dict:
        """Get recruitment pipeline health metrics."""
        job_filter = [Job.organization_id == organization_id] if organization_id else []
        active_jobs = (
            await self._session.execute(
                select(func.count())
                .select_from(Job)
                .where(*job_filter, Job.status == JobStatus.ACTIVE),
            )
        ).scalar_one()

        pending_reviews = (
            await self._session.execute(
                select(func.count())
                .select_from(Application)
                .join(Job, Application.job_id == Job.id)
                .where(*job_filter, Application.status == ApplicationStatus.APPLIED),
            )
        ).scalar_one()

        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        interviews_this_week = (
            await self._session.execute(
                select(func.count())
                .select_from(InterviewSchedule)
                .join(Job, InterviewSchedule.job_id == Job.id)
                .where(*job_filter, InterviewSchedule.scheduled_at >= week_start),
            )
        ).scalar_one()

        return {
            "active_jobs": active_jobs,
            "pending_reviews": pending_reviews,
            "interviews_this_week": interviews_this_week,
            "avg_time_to_hire_days": None,
        }
