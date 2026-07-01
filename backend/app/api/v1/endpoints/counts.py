"""
Sidebar Count Endpoints — unseen/new item counts for badge display.

Counts items created AFTER the user's last_seen_at for each section.
Badge shows 0 (hidden) once the user opens the page.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.application import Application, ApplicationStatus
from app.models.interview_schedule import InterviewSchedule
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.resume import Resume
from app.models.user_page_view import UserPageView

router = APIRouter()


# ── Helpers ─────────────────────────────────────────────────


async def _get_last_seen(
    session: AsyncSession, user_id: uuid.UUID, section: str,
) -> datetime | None:
    """Get the last_seen_at timestamp for a user+section pair."""
    result = await session.execute(
        select(UserPageView.last_seen_at).where(
            UserPageView.user_id == user_id,
            UserPageView.section == section,
        )
    )
    return result.scalar_one_or_none()


async def _mark_seen(
    session: AsyncSession, user_id: uuid.UUID, section: str,
) -> None:
    """Upsert the last_seen_at timestamp to now()."""
    existing = await session.execute(
        select(UserPageView.id).where(
            UserPageView.user_id == user_id,
            UserPageView.section == section,
        )
    )
    row_id = existing.scalar_one_or_none()
    now = datetime.utcnow()

    if row_id:
        await session.execute(
            update(UserPageView)
            .where(UserPageView.id == row_id)
            .values(last_seen_at=now, updated_at=now)
        )
    else:
        page_view = UserPageView(
            user_id=user_id,
            section=section,
            last_seen_at=now,
        )
        session.add(page_view)

    await session.commit()


# ── Schemas ─────────────────────────────────────────────────


class MarkSeenRequest(BaseModel):
    section: str


# ── Endpoints ───────────────────────────────────────────────


@router.get("/sidebar", summary="Get unseen sidebar counts for current user")
async def get_sidebar_counts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Return role-specific unseen/new item counts."""

    # Notifications (always unread count, already tracked by is_read)
    unread_notifications = (
        await session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == current_user.id,
                Notification.is_read == False,  # noqa: E712
            )
        )
    ).scalar() or 0

    if current_user.role == UserRole.RECRUITER:
        # New applications since last viewed
        last_seen = await _get_last_seen(session, current_user.id, "recruiter_applications")
        apps_query = (
            select(func.count(Application.id))
            .join(Job, Application.job_id == Job.id)
            .where(Job.recruiter_id == current_user.id)
        )
        if last_seen:
            apps_query = apps_query.where(Application.applied_at > last_seen)
        new_applications = (await session.execute(apps_query)).scalar() or 0

        return {
            "applications": new_applications,
            "notifications": unread_notifications,
        }

    elif current_user.role == UserRole.HR_MANAGER:
        # New candidates (screened+) since last viewed
        last_seen_cand = await _get_last_seen(session, current_user.id, "hr_candidates")
        cand_query = (
            select(func.count(Application.id))
            .join(Job, Application.job_id == Job.id)
            .where(
                Job.organization_id == current_user.organization_id,
                Application.status.in_([
                    ApplicationStatus.SCREENED,
                    ApplicationStatus.SHORTLISTED,
                    ApplicationStatus.INTERVIEW_SCHEDULED,
                    ApplicationStatus.INTERVIEW_COMPLETED,
                    ApplicationStatus.SELECTED,
                ]),
            )
        )
        if last_seen_cand:
            cand_query = cand_query.where(Application.updated_at > last_seen_cand)
        new_candidates = (await session.execute(cand_query)).scalar() or 0

        # New interviews since last viewed
        last_seen_int = await _get_last_seen(session, current_user.id, "hr_interviews")
        int_query = (
            select(func.count(InterviewSchedule.id))
            .join(Job, InterviewSchedule.job_id == Job.id)
            .where(Job.organization_id == current_user.organization_id)
        )
        if last_seen_int:
            int_query = int_query.where(InterviewSchedule.created_at > last_seen_int)
        new_interviews = (await session.execute(int_query)).scalar() or 0

        return {
            "candidates": new_candidates,
            "interviews": new_interviews,
            "notifications": unread_notifications,
        }

    elif current_user.role == UserRole.CANDIDATE:
        # New jobs since last viewed
        last_seen_jobs = await _get_last_seen(session, current_user.id, "candidate_jobs")
        jobs_query = select(func.count(Job.id)).where(Job.status == "active")
        if last_seen_jobs:
            jobs_query = jobs_query.where(Job.created_at > last_seen_jobs)
        new_jobs = (await session.execute(jobs_query)).scalar() or 0

        # Application status updates since last viewed
        last_seen_apps = await _get_last_seen(session, current_user.id, "candidate_applications")
        apps_query = (
            select(func.count(Application.id)).where(
                Application.candidate_id == current_user.id,
                Application.status != ApplicationStatus.APPLIED,  # Only status changes
            )
        )
        if last_seen_apps:
            apps_query = apps_query.where(Application.updated_at > last_seen_apps)
        new_app_updates = (await session.execute(apps_query)).scalar() or 0

        return {
            "jobs": new_jobs,
            "applications": new_app_updates,
            "notifications": unread_notifications,
        }

    elif current_user.role == UserRole.ADMIN:
        # New users since last viewed
        last_seen_users = await _get_last_seen(session, current_user.id, "admin_users")
        users_query = select(func.count(User.id))
        if last_seen_users:
            users_query = users_query.where(User.created_at > last_seen_users)
        new_users = (await session.execute(users_query)).scalar() or 0

        return {
            "users": new_users,
            "notifications": unread_notifications,
        }

    return {"notifications": unread_notifications}


@router.post("/mark-seen", summary="Mark a sidebar section as viewed")
async def mark_section_seen(
    body: MarkSeenRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Record that the user has viewed a specific section, resetting its badge."""
    await _mark_seen(session, current_user.id, body.section)
    return {"status": "ok", "section": body.section}
