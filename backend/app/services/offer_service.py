"""
Offer Letter Service — generates and manages demo ATS offer letter PDFs.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.user import User

logger = structlog.get_logger(__name__)

OFFERS_DIR = Path("uploads/offers")
OFFERS_DIR.mkdir(parents=True, exist_ok=True)


class OfferService:
    """Generates demo ATS offer letter PDFs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_offer_letter(self, application_id: uuid.UUID) -> str:
        """Generate an offer letter PDF for a selected application.
        
        Returns the file path of the generated PDF.
        """
        application = (
            await self._session.execute(
                select(Application)
                .where(Application.id == application_id)
            )
        ).scalar_one_or_none()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )
        if application.status != ApplicationStatus.SELECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offer letter can only be generated for selected candidates.",
            )

        # Load related data
        job = (
            await self._session.execute(
                select(Job).where(Job.id == application.job_id)
            )
        ).scalar_one_or_none()
        candidate = (
            await self._session.execute(
                select(User).where(User.id == application.candidate_id)
            )
        ).scalar_one_or_none()

        if not job or not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job or candidate not found.",
            )

        org_name = "RecruitGen AI"
        if job.organization:
            org_name = job.organization.name or org_name

        candidate_name = candidate.full_name
        role = job.title
        salary = f"₹{int(job.salary_max):,}" if job.salary_max else "As discussed"
        offer_date = datetime.utcnow().strftime("%B %d, %Y")
        joining_date = (datetime.utcnow() + timedelta(days=30)).strftime("%B %d, %Y")

        file_path = OFFERS_DIR / f"{application_id}.pdf"
        self._generate_pdf(
            str(file_path),
            candidate_name=candidate_name,
            role=role,
            org_name=org_name,
            salary=salary,
            offer_date=offer_date,
            joining_date=joining_date,
        )

        logger.info(
            "offer_letter_generated",
            application_id=str(application_id),
            file_path=str(file_path),
        )
        return str(file_path)

    def _generate_pdf(
        self,
        file_path: str,
        *,
        candidate_name: str,
        role: str,
        org_name: str,
        salary: str,
        offer_date: str,
        joining_date: str,
    ) -> None:
        """Generate the actual PDF file using reportlab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch, cm
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=2 * cm,
            leftMargin=2.5 * cm,
            rightMargin=2.5 * cm,
        )

        styles = getSampleStyleSheet()
        blue = HexColor("#1e40af")
        dark = HexColor("#0f172a")
        gray = HexColor("#64748b")

        # Custom styles
        title_style = ParagraphStyle(
            "OfferTitle",
            parent=styles["Title"],
            fontSize=24,
            textColor=blue,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "OfferSubtitle",
            parent=styles["Normal"],
            fontSize=14,
            textColor=gray,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        body_style = ParagraphStyle(
            "OfferBody",
            parent=styles["Normal"],
            fontSize=11,
            textColor=dark,
            leading=18,
            spaceAfter=12,
        )
        label_style = ParagraphStyle(
            "OfferLabel",
            parent=styles["Normal"],
            fontSize=10,
            textColor=gray,
        )
        value_style = ParagraphStyle(
            "OfferValue",
            parent=styles["Normal"],
            fontSize=11,
            textColor=dark,
            fontName="Helvetica-Bold",
        )
        footer_style = ParagraphStyle(
            "OfferFooter",
            parent=styles["Normal"],
            fontSize=9,
            textColor=gray,
            alignment=TA_CENTER,
        )

        elements = []

        # Header
        elements.append(Paragraph("RecruitGen AI", title_style))
        elements.append(Paragraph("Offer Letter", subtitle_style))
        elements.append(HRFlowable(width="100%", color=blue, thickness=2, spaceAfter=20))

        # Date
        elements.append(Paragraph(f"Date: {offer_date}", body_style))
        elements.append(Spacer(1, 12))

        # Greeting
        elements.append(Paragraph(f"Dear <b>{candidate_name}</b>,", body_style))
        elements.append(Spacer(1, 8))

        # Congratulations
        elements.append(Paragraph(
            "Congratulations! We are pleased to inform you that you have been selected "
            "for the following position. We are confident that your skills and experience "
            "will be a valuable addition to our team.",
            body_style,
        ))
        elements.append(Spacer(1, 16))

        # Offer Details Table
        table_data = [
            [Paragraph("Role", label_style), Paragraph(role, value_style)],
            [Paragraph("Company", label_style), Paragraph(org_name, value_style)],
            [Paragraph("Salary", label_style), Paragraph(salary, value_style)],
            [Paragraph("Joining Date", label_style), Paragraph(joining_date, value_style)],
        ]
        table = Table(table_data, colWidths=[3 * cm, 12 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, -1), dark),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [HexColor("#ffffff"), HexColor("#f8fafc")]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 24))

        # Closing
        elements.append(Paragraph(
            "We look forward to working with you and wish you the very best "
            "in your new role. Please do not hesitate to reach out if you have "
            "any questions.",
            body_style,
        ))
        elements.append(Spacer(1, 24))

        elements.append(Paragraph("Warm regards,", body_style))
        elements.append(Paragraph(f"<b>{org_name}</b>", body_style))
        elements.append(Paragraph("Human Resources Department", body_style))

        # Footer
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", color=HexColor("#cbd5e1"), thickness=0.5, spaceAfter=12))
        elements.append(Paragraph(
            "This is a system-generated document from RecruitGen AI. "
            "This offer letter is for demonstration purposes only.",
            footer_style,
        ))

        doc.build(elements)

    def get_offer_path(self, application_id: uuid.UUID) -> str | None:
        """Check if an offer letter PDF exists."""
        file_path = OFFERS_DIR / f"{application_id}.pdf"
        if file_path.exists():
            return str(file_path)
        return None
