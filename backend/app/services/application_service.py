"""
Application Service — apply, list, status management.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile
from app.models.candidate_match import CandidateMatch
from app.models.candidate_ranking import CandidateRanking
from app.models.job import JobStatus
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate

logger = structlog.get_logger(__name__)


class ApplicationService:
    """Orchestrates job application workflow and authorization."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._app_repo = ApplicationRepository(session)
        self._job_repo = JobRepository(session)

    # ── candidate actions ───────────────────────────────────

    async def apply(
        self, payload: ApplicationCreate, candidate: User,
    ) -> Application:
        """Submit a new application on behalf of a candidate.

        Raises:
            HTTPException 404: job not found.
            HTTPException 400: job is not active.
            HTTPException 409: candidate already applied.
        """
        # Verify the job exists and is active
        job = await self._job_repo.get_by_id(payload.job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
        if job.status != JobStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This job is not accepting applications.",
            )

        # Prevent duplicate applications
        if await self._app_repo.exists(candidate.id, payload.job_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied for this job.",
            )

        application = Application(
            job_id=payload.job_id,
            candidate_id=candidate.id,
        )
        application = await self._app_repo.create(application)
        await self._session.commit()
        await self._session.refresh(application)

        logger.info(
            "application_submitted",
            application_id=str(application.id),
            job_id=str(payload.job_id),
            candidate_id=str(candidate.id),
        )
        return application

    async def list_my_applications(
        self,
        candidate: User,
        *,
        status_filter: ApplicationStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Application]:
        """Return all applications for the authenticated candidate."""
        return await self._app_repo.list_by_candidate(
            candidate.id, status=status_filter, skip=skip, limit=limit,
        )

    async def list_all_applications(
        self,
        user: User,
        *,
        status_filter: ApplicationStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Application]:
        """Return all applications visible to the admin/recruiter.

        Admin sees all applications in their organization.
        Recruiter sees applications for their own jobs only.
        """
        if user.role in (UserRole.ADMIN, UserRole.HR_MANAGER):
            return await self._app_repo.list_all(
                organization_id=user.organization_id,
                status=status_filter, skip=skip, limit=limit,
            )
        else:
            # Recruiter — only their jobs
            return await self._app_repo.list_all(
                recruiter_id=user.id,
                status=status_filter, skip=skip, limit=limit,
            )

    async def list_pipeline(
        self,
        user: User,
        *,
        job_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 200,
    ) -> list[Application]:
        """Return organization-scoped candidates who reached the HR pipeline."""
        pipeline_statuses = (
            ApplicationStatus.SCREENED,
            ApplicationStatus.SHORTLISTED,
            ApplicationStatus.INTERVIEW_SCHEDULED,
            ApplicationStatus.INTERVIEW_COMPLETED,
            ApplicationStatus.SELECTED,
        )
        filters = {
            "statuses": pipeline_statuses,
            "job_id": job_id,
            "skip": skip,
            "limit": limit,
        }
        if user.role in (UserRole.ADMIN, UserRole.HR_MANAGER):
            return await self._app_repo.list_all(
                organization_id=user.organization_id,
                **filters,
            )
        if user.role == UserRole.RECRUITER:
            return await self._app_repo.list_all(
                recruiter_id=user.id,
                **filters,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view the candidate pipeline.",
        )

    async def enrich_applications(
        self, applications: list[Application],
    ) -> list[dict]:
        """Join user-based applications to profile-based AI workflow records."""
        if not applications:
            return []

        user_ids = {application.candidate_id for application in applications}
        profile_rows = (
            await self._session.execute(
                select(CandidateProfile, Resume.candidate_id)
                .join(Resume, CandidateProfile.resume_id == Resume.id)
                .where(Resume.candidate_id.in_(user_ids))
                .order_by(CandidateProfile.updated_at.desc())
            )
        ).all()
        profiles_by_user: dict[uuid.UUID, CandidateProfile] = {}
        for profile, user_id in profile_rows:
            profiles_by_user.setdefault(user_id, profile)

        profile_ids = {profile.id for profile in profiles_by_user.values()}
        job_ids = {application.job_id for application in applications}
        matches = []
        rankings = []
        if profile_ids:
            matches = list((
                await self._session.execute(
                    select(CandidateMatch).where(
                        CandidateMatch.candidate_id.in_(profile_ids),
                        CandidateMatch.job_id.in_(job_ids),
                    )
                )
            ).scalars().all())
            rankings = list((
                await self._session.execute(
                    select(CandidateRanking).where(
                        CandidateRanking.candidate_id.in_(profile_ids),
                        CandidateRanking.job_id.in_(job_ids),
                    )
                )
            ).scalars().all())

        match_map = {(item.candidate_id, item.job_id): item for item in matches}
        ranking_map = {(item.candidate_id, item.job_id): item for item in rankings}
        enriched: list[dict] = []
        for application in applications:
            profile = profiles_by_user.get(application.candidate_id)
            match = match_map.get((profile.id, application.job_id)) if profile else None
            ranking = ranking_map.get((profile.id, application.job_id)) if profile else None
            enriched.append({
                "id": application.id,
                "job_id": application.job_id,
                "candidate_id": application.candidate_id,
                "status": application.status,
                "applied_at": application.applied_at,
                "updated_at": application.updated_at,
                "selected_at": application.selected_at,
                "selected_by": application.selected_by,
                "rejected_at": application.rejected_at,
                "rejected_by": application.rejected_by,
                "candidate_name": application.candidate.full_name if application.candidate else None,
                "job_title": application.job.title if application.job else None,
                "candidate_profile_id": profile.id if profile else None,
                "overall_match_score": match.overall_match_score if match else None,
                "skill_match_score": match.skill_match_score if match else None,
                "experience_match_score": match.experience_match_score if match else None,
                "rank_position": ranking.rank_position if ranking else None,
                "final_score": ranking.final_score if ranking else None,
            })
        return enriched

    # ── recruiter / admin actions ───────────────────────────

    async def list_job_applications(
        self,
        job_id: uuid.UUID,
        user: User,
        *,
        status_filter: ApplicationStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Application]:
        """Return applications for a job (recruiter's own jobs or admin's org).

        Raises:
            HTTPException 404: job not found.
            HTTPException 403: not authorized.
        """
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )

        # Authorization: admin sees org jobs, recruiter sees own jobs
        if user.role in (UserRole.ADMIN, UserRole.HR_MANAGER):
            if job.organization_id != user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view applications for this job.",
                )
        elif user.role == UserRole.RECRUITER:
            if job.recruiter_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view applications for this job.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidates cannot view applications for a job.",
            )

        return await self._app_repo.list_by_job(
            job_id, status=status_filter, skip=skip, limit=limit,
        )

    async def update_status(
        self,
        application_id: uuid.UUID,
        payload: ApplicationStatusUpdate,
        user: User,
    ) -> Application:
        """Update the status of an application (recruiter / admin only).

        Raises:
            HTTPException 404: application not found.
            HTTPException 403: not authorized.
        """
        application = await self._app_repo.get_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )

        # Load the related job to check ownership
        job = await self._job_repo.get_by_id(application.job_id)
        if user.role in (UserRole.ADMIN, UserRole.HR_MANAGER):
            if not job or job.organization_id != user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this application.",
                )
        elif user.role == UserRole.RECRUITER:
            if not job or job.recruiter_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this application.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidates cannot update application status.",
            )

        if payload.status == application.status:
            logger.info(
                "application_status_update_idempotent",
                application_id=str(application_id),
                status=application.status.value,
            )
            return application

        # ── Pipeline stage enforcement ──────────────────────────
        VALID_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
            ApplicationStatus.APPLIED: {
                ApplicationStatus.SCREENED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.SCREENED: {
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.SHORTLISTED: {
                ApplicationStatus.INTERVIEW_SCHEDULED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.INTERVIEW_SCHEDULED: {
                ApplicationStatus.INTERVIEW_COMPLETED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.INTERVIEW_COMPLETED: {
                ApplicationStatus.SELECTED,
                ApplicationStatus.REJECTED,
            },
        }
        allowed = VALID_TRANSITIONS.get(application.status, set())
        if payload.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot transition from '{application.status.value}' to '{payload.status.value}'. "
                       f"Valid next stages: {', '.join(s.value for s in sorted(allowed, key=lambda x: x.value)) if allowed else 'none (terminal state)'}.",
            )

        previous = application.status
        application.status = payload.status

        # ── Set hiring decision metadata ────────────────────────
        if payload.status == ApplicationStatus.SELECTED:
            application.selected_at = datetime.utcnow()
            application.selected_by = user.id
        elif payload.status == ApplicationStatus.REJECTED:
            application.rejected_at = datetime.utcnow()
            application.rejected_by = user.id

        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(application)

        logger.info(
            "application_status_updated",
            application_id=str(application_id),
            previous_status=previous.value,
            new_status=payload.status.value,
        )

        # ── Send notifications (non-blocking) ──────────────────
        try:
            from app.services.communication_service import CommunicationService

            comms = CommunicationService(self._session)
            candidate_id = application.candidate_id
            job_id = application.job_id
            job_title = job.title if job else "Unknown Position"
            candidate_name = (
                application.candidate.full_name
                if application.candidate
                else "Unknown Candidate"
            )
            recruiter_id = job.recruiter_id if job else None

            if payload.status == ApplicationStatus.SCREENED:
                await comms.send_screening_notification(
                    candidate_id, job_id, job_title,
                )
            elif payload.status == ApplicationStatus.SHORTLISTED:
                await comms.send_shortlist_notification(
                    candidate_id, job_id, job_title,
                )
            elif payload.status == ApplicationStatus.INTERVIEW_SCHEDULED:
                await comms.send_interview_invitation(
                    candidate_id, job_id, job_title, {},
                )
            elif payload.status == ApplicationStatus.INTERVIEW_COMPLETED:
                await comms.send_interview_completed_notification(
                    candidate_id, job_id, job_title,
                )
            elif payload.status == ApplicationStatus.SELECTED:
                await comms.send_selection_notification(
                    candidate_id, job_id, job_title,
                )
                if recruiter_id:
                    await comms.send_recruiter_hire_notification(
                        recruiter_id, candidate_name, job_title, job_id,
                    )
            elif payload.status == ApplicationStatus.REJECTED:
                await comms.send_rejection_notification(
                    candidate_id, job_id, job_title,
                )
                if recruiter_id:
                    await comms.send_recruiter_reject_notification(
                        recruiter_id, candidate_name, job_title, job_id,
                    )
        except Exception:
            logger.exception(
                "notification_send_failed",
                application_id=str(application_id),
                new_status=payload.status.value,
            )

        return application
