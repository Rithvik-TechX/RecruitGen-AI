"""
Communication Service — notifications and mock email delivery.

Designed with an EmailProvider abstraction so SMTP/SendGrid
can be plugged in later without changing the service logic.
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repositories.notification_repository import NotificationRepository

logger = structlog.get_logger(__name__)


# ── Email Provider Abstraction ──────────────────────────────


class EmailProvider(Protocol):
    """Abstract email sender — implement for SMTP, SendGrid, etc."""

    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailProvider:
    """Mock email provider that logs emails to the console."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "email_sent",
            to=to,
            subject=subject,
            body_preview=body[:200] if body else "",
        )


# ── Communication Service ──────────────────────────────────


class CommunicationService:
    """Manages notifications and email communication."""

    def __init__(
        self,
        session: AsyncSession,
        email_provider: EmailProvider | None = None,
    ) -> None:
        self._session = session
        self._repo = NotificationRepository(session)
        self._email = email_provider or ConsoleEmailProvider()

    async def _create_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        """Create a notification and send a mock email."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            metadata_=metadata,
        )
        notification = await self._repo.create(notification)
        await self._session.commit()

        # Fire mock email
        await self._email.send(
            to=str(user_id),
            subject=title,
            body=message,
        )
        return notification

    async def send_shortlist_notification(
        self, user_id: uuid.UUID, job_id: uuid.UUID, job_title: str,
    ) -> Notification:
        """Notify a candidate they've been shortlisted."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.SHORTLISTED,
            title=f"Congratulations! You've been shortlisted for {job_title}",
            message=(
                f"We're pleased to inform you that your application for the "
                f"position of {job_title} has been shortlisted. Our team will "
                f"be in touch regarding next steps."
            ),
            metadata={"job_id": str(job_id)},
        )

    async def send_rejection_notification(
        self, user_id: uuid.UUID, job_id: uuid.UUID, job_title: str,
    ) -> Notification:
        """Notify a candidate of rejection."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.REJECTION,
            title=f"Application Update — {job_title}",
            message=(
                f"Thank you for your interest in the {job_title} position. "
                f"After careful consideration, we have decided to move forward "
                f"with other candidates. We encourage you to apply for future "
                f"openings that match your skills."
            ),
            metadata={"job_id": str(job_id)},
        )

    async def send_interview_invitation(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_title: str,
        interview_details: dict[str, Any],
    ) -> Notification:
        """Notify a candidate about an interview invitation."""
        scheduled_at = interview_details.get("scheduled_at", "TBD")
        interview_type = interview_details.get("interview_type", "video")
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.INTERVIEW_INVITE,
            title=f"Interview Invitation — {job_title}",
            message=(
                f"You have been invited for a {interview_type} interview "
                f"for the {job_title} position scheduled at {scheduled_at}. "
                f"Please confirm your availability."
            ),
            metadata={"job_id": str(job_id), **interview_details},
        )

    async def send_offer_notification(
        self, user_id: uuid.UUID, job_id: uuid.UUID, job_title: str,
    ) -> Notification:
        """Notify a candidate about a job offer."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.OFFER,
            title=f"Job Offer — {job_title}",
            message=(
                f"We are delighted to extend a formal offer for the position "
                f"of {job_title}. Please review the offer details and respond "
                f"at your earliest convenience."
            ),
            metadata={"job_id": str(job_id)},
        )

    async def send_screening_notification(
        self, user_id: uuid.UUID, job_id: uuid.UUID, job_title: str,
    ) -> Notification:
        """Notify a candidate that their application has been screened."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.SCREENING,
            title=f"Application Screened — {job_title}",
            message=(
                f"Your application for {job_title} has been screened. "
                f"Our team is reviewing your qualifications and will be "
                f"in touch with next steps."
            ),
            metadata={"job_id": str(job_id)},
        )

    async def send_application_submitted_notification(
        self,
        recruiter_user_id: uuid.UUID,
        candidate_name: str,
        job_title: str,
        job_id: uuid.UUID,
    ) -> Notification:
        """Notify a recruiter about a new application submission."""
        return await self._create_notification(
            user_id=recruiter_user_id,
            notification_type=NotificationType.APPLICATION_SUBMITTED,
            title=f"New Application — {job_title}",
            message=(
                f"New application from {candidate_name} for {job_title}. "
                f"Please review the candidate's profile and qualifications."
            ),
            metadata={"job_id": str(job_id), "candidate_name": candidate_name},
        )

    async def send_interview_completed_notification(
        self, user_id: uuid.UUID, job_id: uuid.UUID, job_title: str,
    ) -> Notification:
        """Notify a candidate that their interview has been completed."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.INTERVIEW_COMPLETED,
            title=f"Interview Completed — {job_title}",
            message=(
                f"Your interview for {job_title} has been completed. "
                f"Thank you for your time. We will follow up with results shortly."
            ),
            metadata={"job_id": str(job_id)},
        )

    async def send_selection_notification(
        self, user_id: uuid.UUID, job_id: uuid.UUID, job_title: str,
    ) -> Notification:
        """Notify a candidate that they have been selected."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.SELECTED,
            title=f"Congratulations! You have been selected for {job_title}",
            message=(
                f"Congratulations! You have been selected for {job_title}. "
                f"Our team will reach out to you with further details regarding "
                f"the next steps in the onboarding process."
            ),
            metadata={"job_id": str(job_id)},
        )

    async def send_resume_parsed_notification(
        self, user_id: uuid.UUID,
    ) -> Notification:
        """Notify a candidate that their resume has been parsed successfully."""
        return await self._create_notification(
            user_id=user_id,
            notification_type=NotificationType.RESUME_PARSED,
            title="Resume Parsed Successfully",
            message=(
                "Your resume has been parsed successfully. Your profile has "
                "been updated with the extracted information. Please review "
                "your profile to ensure accuracy."
            ),
        )

    async def send_evaluation_ready_notification(
        self,
        hr_user_id: uuid.UUID,
        candidate_name: str,
        job_title: str,
        job_id: uuid.UUID,
    ) -> Notification:
        """Notify HR that a candidate is ready for evaluation."""
        return await self._create_notification(
            user_id=hr_user_id,
            notification_type=NotificationType.APPLICATION_UPDATE,
            title=f"Candidate Ready for Evaluation — {job_title}",
            message=(
                f"Candidate {candidate_name} is ready for evaluation "
                f"for {job_title}. Please review the candidate's profile "
                f"and proceed with the evaluation process."
            ),
            metadata={"job_id": str(job_id), "candidate_name": candidate_name},
        )

    async def send_recommendation_generated_notification(
        self,
        hr_user_id: uuid.UUID,
        candidate_name: str,
        job_title: str,
        job_id: uuid.UUID,
    ) -> Notification:
        """Notify HR that a recommendation has been generated for a candidate."""
        return await self._create_notification(
            user_id=hr_user_id,
            notification_type=NotificationType.RECOMMENDATION_GENERATED,
            title=f"Recommendation Generated — {job_title}",
            message=(
                f"Recommendation generated for {candidate_name} for "
                f"{job_title}. Please review the recommendation and take "
                f"appropriate action."
            ),
            metadata={"job_id": str(job_id), "candidate_name": candidate_name},
        )

    async def send_recruiter_hire_notification(
        self,
        recruiter_user_id: uuid.UUID,
        candidate_name: str,
        job_title: str,
        job_id: uuid.UUID,
    ) -> Notification:
        """Notify a recruiter that a candidate has been selected."""
        return await self._create_notification(
            user_id=recruiter_user_id,
            notification_type=NotificationType.SELECTED,
            title=f"Candidate Selected — {job_title}",
            message=(
                f"Candidate {candidate_name} has been selected for "
                f"{job_title}. Please proceed with the offer process."
            ),
            metadata={"job_id": str(job_id), "candidate_name": candidate_name},
        )

    async def send_recruiter_reject_notification(
        self,
        recruiter_user_id: uuid.UUID,
        candidate_name: str,
        job_title: str,
        job_id: uuid.UUID,
    ) -> Notification:
        """Notify a recruiter that a candidate has been rejected."""
        return await self._create_notification(
            user_id=recruiter_user_id,
            notification_type=NotificationType.REJECTION,
            title=f"Candidate Rejected — {job_title}",
            message=(
                f"Candidate {candidate_name} has been rejected for "
                f"{job_title}."
            ),
            metadata={"job_id": str(job_id), "candidate_name": candidate_name},
        )

    async def list_notifications(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 50,
    ) -> tuple[list[Notification], int, int]:
        """List notifications with unread and total counts."""
        notifications = await self._repo.list_by_user(
            user_id, skip=skip, limit=limit,
        )
        unread = await self._repo.count_unread(user_id)
        total = len(notifications)
        return notifications, unread, total

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get unread notification count."""
        return await self._repo.count_unread(user_id)

    async def mark_read(self, notification_id: uuid.UUID) -> Notification:
        """Mark a single notification as read."""
        notification = await self._repo.mark_as_read(notification_id)
        if not notification:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        await self._session.commit()
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications as read for a user. Returns count updated."""
        from sqlalchemy import update

        result = await self._session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        await self._session.commit()
        return result.rowcount

