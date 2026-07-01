"""
Report Endpoints — generate, list, download reports.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_recruiter_or_hr
from app.db.session import get_db
from app.models.report import ReportType
from app.models.user import User
from app.schemas.report import (
    ReportListItem,
    ReportListResponse,
    ReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


class GenericReportRequest(BaseModel):
    """Body for the generic POST /reports endpoint."""
    report_type: str
    title: str | None = None


async def serialize_report(
    service: ReportService, report,
) -> ReportResponse:
    """Convert persistence data into the presentation report contract."""
    return ReportResponse(
        id=report.id,
        report_type=report.report_type,
        title=report.title,
        summary=report.summary,
        data=await service.presentation_data(report),
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post(
    "/",
    response_model=ReportResponse,
    summary="Generate a generic report",
)
async def generate_generic_report(
    payload: GenericReportRequest,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Generate a summary-level report without requiring a specific ID.

    Useful for analytics, overview, and org-wide reports.
    """
    try:
        report_type = ReportType(payload.report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported report type.",
        )
    if report_type not in (ReportType.HIRING, ReportType.ANALYTICS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Organization reports support hiring and analytics types.",
        )

    service = ReportService(session)
    report = await service.generate_organization_report(
        report_type,
        current_user,
        title=payload.title,
    )
    return await serialize_report(service, report)


@router.post(
    "/candidate/{candidate_id}",
    response_model=ReportResponse,
    summary="Generate candidate report",
)
async def generate_candidate_report(
    candidate_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    service = ReportService(session)
    report = await service.generate_candidate_report(candidate_id, current_user.id)
    return await serialize_report(service, report)


@router.post(
    "/hiring/{job_id}",
    response_model=ReportResponse,
    summary="Generate hiring report",
)
async def generate_hiring_report(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    service = ReportService(session)
    report = await service.generate_hiring_report(job_id, current_user.id)
    return await serialize_report(service, report)


@router.post(
    "/match/{job_id}",
    response_model=ReportResponse,
    summary="Generate match report",
)
async def generate_match_report(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    service = ReportService(session)
    report = await service.generate_match_report(job_id, current_user.id)
    return await serialize_report(service, report)


@router.get("/", response_model=ReportListResponse, summary="List reports")
async def list_reports(
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> ReportListResponse:
    service = ReportService(session)
    reports, total = await service.list_reports(
        current_user.id, skip=skip, limit=limit,
    )
    return ReportListResponse(
        reports=[
            ReportListItem(
                id=report.id,
                report_type=report.report_type,
                title=report.title,
                summary=report.summary,
                organization_name=report.author.organization.name,
                report_period=(
                    (report.content or {}).get("header", {}).get("report_period")
                    or report.created_at.strftime("%b %d, %Y")
                ),
                status=report.status,
                created_at=report.created_at,
            )
            for report in reports
        ],
        total_count=total,
    )


@router.get("/{report_id}", response_model=ReportResponse, summary="Get report")
async def get_report(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    service = ReportService(session)
    report = await service.get_report(report_id, user_id=current_user.id)
    return await serialize_report(service, report)


@router.get("/{report_id}/download", summary="Download report PDF")
async def download_report(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    service = ReportService(session)
    file_path = await service.export_pdf(report_id, user_id=current_user.id)
    return FileResponse(
        path=file_path,
        filename=f"report_{report_id}.pdf",
        media_type="application/pdf",
    )


@router.get("/{report_id}/excel", summary="Download report Excel workbook")
async def download_report_excel(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    service = ReportService(session)
    file_path = await service.export_excel(report_id, user_id=current_user.id)
    return FileResponse(
        path=file_path,
        filename=f"report_{report_id}.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


@router.get("/{report_id}/csv", summary="Download report CSV")
async def download_report_csv(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(admin_recruiter_or_hr)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    service = ReportService(session)
    file_path = await service.export_csv(report_id, user_id=current_user.id)
    return FileResponse(
        path=file_path,
        filename=f"report_{report_id}.csv",
        media_type="text/csv",
    )
