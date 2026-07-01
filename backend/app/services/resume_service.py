"""
Resume Service — upload and retrieval.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import structlog
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.user import User
from app.repositories.resume_repository import ResumeRepository

logger = structlog.get_logger(__name__)

UPLOAD_DIR = Path("uploads/resumes")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class ResumeService:
    """Handles resume file uploads and retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._resume_repo = ResumeRepository(session)

    async def upload(
        self, file: UploadFile, candidate: User,
    ) -> Resume:
        """Save an uploaded resume to disk and create a DB record.

        Raises:
            HTTPException 400: invalid file type or size exceeded.
        """
        # ── Validate content type ───────────────────────────
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type '{file.content_type}'. "
                    "Allowed: PDF, DOC, DOCX."
                ),
            )

        # ── Read content and check size ─────────────────────
        content = await file.read()
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large ({file_size} bytes). Maximum is {MAX_FILE_SIZE} bytes.",
            )

        # ── Write to disk ───────────────────────────────────
        candidate_dir = UPLOAD_DIR / str(candidate.id)
        candidate_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        dest = candidate_dir / safe_name
        dest.write_bytes(content)

        relative_path = str(dest)

        # ── Persist metadata ────────────────────────────────
        resume = Resume(
            candidate_id=candidate.id,
            file_name=file.filename or "unknown",
            file_path=relative_path,
            file_type=file.content_type or "application/octet-stream",
            file_size=file_size,
        )
        resume = await self._resume_repo.create(resume)
        await self._session.commit()
        await self._session.refresh(resume)

        logger.info(
            "resume_uploaded",
            resume_id=str(resume.id),
            candidate_id=str(candidate.id),
            file_name=file.filename,
            file_size=file_size,
        )
        return resume

    async def list_my_resumes(
        self,
        candidate: User,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Resume]:
        """Return all resumes uploaded by the authenticated candidate."""
        return await self._resume_repo.list_by_candidate(
            candidate.id, skip=skip, limit=limit,
        )

    async def get_resume(
        self, resume_id: uuid.UUID, user: User,
    ) -> Resume:
        """Retrieve a single resume (owner only).

        Raises:
            HTTPException 404: not found.
            HTTPException 403: not the owner.
        """
        resume = await self._resume_repo.get_by_id(resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )
        if resume.candidate_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resume.",
            )
        return resume
