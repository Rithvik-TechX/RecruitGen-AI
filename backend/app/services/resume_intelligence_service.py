"""
Resume Intelligence Service — parse resumes, build candidate profiles.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import (
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateProfile,
    CandidateProject,
    CandidateSkill,
    ParserSource,
    ParsingStatus,
)
from app.repositories.candidate_repository import (
    CandidateCertificationRepository,
    CandidateEducationRepository,
    CandidateExperienceRepository,
    CandidateProfileRepository,
    CandidateProjectRepository,
    CandidateSkillRepository,
)
from app.repositories.resume_repository import ResumeRepository
from app.providers.gemini_provider import (
    GeminiServiceError,
    fallback_parse_resume,
    mark_ai_failure,
    merge_resume_parse_results,
    parse_resume_with_gemini,
)
from app.providers.embedding_provider import build_candidate_text, generate_embedding
from app.vector_store.chroma_store import VectorStore
from app.utils.resume_parser import extract_text_from_resume

logger = structlog.get_logger(__name__)


def _build_extraction_statistics(parsed: dict) -> dict[str, int]:
    return {
        "skills": len(parsed.get("skills") or []),
        "education": len(parsed.get("education") or []),
        "experience": len(parsed.get("experience") or []),
        "projects": len(parsed.get("projects") or []),
        "certifications": len(parsed.get("certifications") or []),
        "achievements": len(parsed.get("achievements") or []),
        "internships": len(parsed.get("internships") or []),
        "awards": len(parsed.get("awards") or []),
        "publications": len(parsed.get("publications") or []),
        "research": len(parsed.get("research_experience") or []),
        "links": len(parsed.get("links") or []),
        "languages": len(parsed.get("languages") or []),
    }


def _normalise_profile_url(value: str | None) -> str | None:
    if not value:
        return None
    return value if value.lower().startswith(("http://", "https://")) else f"https://{value}"


class ResumeIntelligenceService:
    """Orchestrates: text extraction → Gemini AI → profile creation → embeddings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._profile_repo = CandidateProfileRepository(session)
        self._skill_repo = CandidateSkillRepository(session)
        self._education_repo = CandidateEducationRepository(session)
        self._experience_repo = CandidateExperienceRepository(session)
        self._project_repo = CandidateProjectRepository(session)
        self._certification_repo = CandidateCertificationRepository(session)
        self._resume_repo = ResumeRepository(session)

    async def parse_resume(self, resume_id: uuid.UUID) -> CandidateProfile:
        """Parse a resume and create / update the candidate profile.

        Steps:
        1. Fetch resume record
        2. Extract text (PDF / DOCX)
        3. Parse with Gemini AI
        4. Create CandidateProfile + related entities
        5. Generate & store embedding in ChromaDB
        """
        # 1 — Get resume
        resume = await self._resume_repo.get_by_id(resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        existing = await self._profile_repo.get_by_resume_id(resume_id)

        # Create / reset profile
        if existing:
            profile = existing
            profile.parsing_status = ParsingStatus.PROCESSING
            await self._delete_profile_details(profile.id)
            await self._session.flush()
        else:
            profile = CandidateProfile(
                resume_id=resume_id,
                full_name="",
                parsing_status=ParsingStatus.PROCESSING,
            )
            profile = await self._profile_repo.create(profile)

        try:
            # 2 — Extract text
            raw_text = extract_text_from_resume(resume.file_path)
            if not raw_text.strip():
                raise ValueError("No text could be extracted from the resume")

            # 3 — Parse with Gemini, then gracefully fall back locally if AI is unavailable
            fallback_parsed = fallback_parse_resume(raw_text)
            try:
                ai_parsed = await parse_resume_with_gemini(raw_text)
                parsed = merge_resume_parse_results(ai_parsed, fallback_parsed)
                parser_source = ParserSource.AI
            except (GeminiServiceError, ValueError) as exc:
                mark_ai_failure(exc, fallback_available=True)
                logger.warning(
                    "resume_ai_fallback_used",
                    resume_id=str(resume_id),
                    error=str(exc),
                )
                parsed = fallback_parsed
                parser_source = ParserSource.FALLBACK
            extraction_statistics = _build_extraction_statistics(parsed)
            personal = parsed.get("personal_details", {})
            achievements = [
                {"title": item.get("title"), "description": item.get("description"), "date": item.get("date")}
                for item in (parsed.get("achievements") or [])
                if isinstance(item, dict) and item.get("title")
            ]
            internships = [
                {
                    "company": item.get("company") or "Not specified",
                    "role": item.get("role") or item.get("title") or "Intern",
                    "duration": item.get("duration"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "description": item.get("description"),
                    "technologies": item.get("technologies") if isinstance(item.get("technologies"), list) else [],
                }
                for item in (parsed.get("internships") or [])
                if isinstance(item, dict)
            ]
            awards = [
                {
                    "title": item.get("title"),
                    "issuer": item.get("issuer"),
                    "date": item.get("date"),
                    "description": item.get("description"),
                }
                for item in (parsed.get("awards") or [])
                if isinstance(item, dict) and item.get("title")
            ]
            publications = [
                {
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "publication_date": item.get("publication_date"),
                    "url": item.get("url"),
                    "description": item.get("description"),
                }
                for item in (parsed.get("publications") or [])
                if isinstance(item, dict) and item.get("title")
            ]
            research_experience = [
                {
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "duration": item.get("duration"),
                }
                for item in (parsed.get("research_experience") or [])
                if isinstance(item, dict) and item.get("title")
            ]
            links = [
                {
                    "link_type": item.get("link_type") or "other",
                    "label": item.get("label"),
                    "url": _normalise_profile_url(item.get("url")),
                }
                for item in (parsed.get("links") or [])
                if isinstance(item, dict) and item.get("url")
            ]
            languages = [
                str(language).strip()
                for language in (parsed.get("languages") or [])
                if str(language).strip()
            ]

            # 4 — Update profile
            profile.full_name = personal.get("full_name") or ""
            profile.email = personal.get("email")
            profile.phone = personal.get("phone")
            profile.linkedin_url = _normalise_profile_url(personal.get("linkedin_url")) or next(
                (item["url"] for item in links if item["link_type"] == "linkedin"),
                None,
            )
            profile.github_url = _normalise_profile_url(personal.get("github_url")) or next(
                (item["url"] for item in links if item["link_type"] == "github"),
                None,
            )
            profile.summary = personal.get("summary")
            profile.raw_text = raw_text
            profile.raw_parsed_data = parsed
            profile.extraction_statistics = extraction_statistics
            profile.parser_source = parser_source
            profile.achievements = achievements
            profile.internships = internships
            profile.awards = awards
            profile.publications = publications
            profile.research_experience = research_experience
            profile.languages = languages
            profile.links = links
            profile.parsing_status = ParsingStatus.COMPLETED
            await self._session.flush()

            # Skills
            skills_data = parsed.get("skills", [])
            for s in skills_data:
                if s.get("skill_name"):
                    self._session.add(CandidateSkill(
                        candidate_id=profile.id,
                        skill_name=s["skill_name"],
                        proficiency_level=s.get("proficiency_level"),
                        category=s.get("category"),
                    ))

            # Education
            for e in parsed.get("education", []):
                if e.get("institution"):
                    self._session.add(CandidateEducation(
                        candidate_id=profile.id,
                        institution=e["institution"],
                        degree=e.get("degree"),
                        field_of_study=e.get("field_of_study"),
                        start_date=e.get("start_date"),
                        end_date=e.get("end_date"),
                        gpa=e.get("gpa"),
                        description=e.get("description"),
                    ))

            # Experience
            experience_data = parsed.get("experience", [])
            for exp in experience_data:
                if exp.get("company") or exp.get("title"):
                    self._session.add(CandidateExperience(
                        candidate_id=profile.id,
                        company=exp.get("company", ""),
                        title=exp.get("title", ""),
                        location=exp.get("location"),
                        start_date=exp.get("start_date"),
                        end_date=exp.get("end_date"),
                        is_current=exp.get("is_current", False),
                        description=exp.get("description"),
                        technologies=exp.get("technologies"),
                    ))

            # Projects
            projects_data = parsed.get("projects", [])
            for p in projects_data:
                project_name = p.get("project_name") or p.get("title")
                if project_name:
                    technologies = p.get("technologies")
                    if isinstance(technologies, list):
                        technologies = ", ".join(str(item) for item in technologies)
                    self._session.add(CandidateProject(
                        candidate_id=profile.id,
                        project_name=project_name,
                        description=p.get("description"),
                        technologies=technologies,
                        year=p.get("year") or p.get("start_date"),
                        url=p.get("url"),
                        start_date=p.get("start_date"),
                        end_date=p.get("end_date"),
                    ))

            # Certifications
            certs_data = parsed.get("certifications", [])
            for c in certs_data:
                if c.get("certification_name"):
                    self._session.add(CandidateCertification(
                        candidate_id=profile.id,
                        certification_name=c["certification_name"],
                        issuing_organization=c.get("issuing_organization"),
                        issue_date=c.get("issue_date"),
                        expiry_date=c.get("expiry_date"),
                        credential_id=c.get("credential_id"),
                        credential_url=c.get("credential_url"),
                    ))

            await self._session.flush()

            # 5 — Generate embedding & store in ChromaDB
            try:
                candidate_text = build_candidate_text({
                    "full_name": personal.get("full_name"),
                    "summary": personal.get("summary"),
                    "skills": skills_data,
                    "experiences": experience_data,
                    "educations": parsed.get("education", []),
                    "projects": projects_data,
                    "certifications": certs_data,
                    "achievements": profile.achievements,
                    "internships": profile.internships,
                    "awards": profile.awards,
                    "publications": profile.publications,
                    "research_experience": profile.research_experience,
                    "languages": profile.languages,
                })
                embedding = generate_embedding(candidate_text)
                VectorStore().upsert_candidate_embedding(
                    candidate_id=str(profile.id),
                    embedding=embedding,
                    metadata={
                        "full_name": personal.get("full_name") or "",
                        "email": personal.get("email") or "",
                        "resume_id": str(resume_id),
                    },
                    document=candidate_text,
                )
            except Exception as exc:
                logger.warning("embedding_generation_failed", error=str(exc))

            await self._session.commit()

            # Reload with relations
            profile = await self._profile_repo.get_by_id_with_details(profile.id)
            logger.info(
                "resume_parsed_successfully",
                resume_id=str(resume_id),
                candidate_id=str(profile.id),
                parser_source=profile.parser_source.value,
                extraction_statistics=profile.extraction_statistics,
            )
            return profile

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("resume_parsing_failed", resume_id=str(resume_id), error=str(exc))
            profile.parsing_status = ParsingStatus.FAILED
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse resume: {exc}",
            ) from exc

    async def get_candidate(self, candidate_id: uuid.UUID) -> CandidateProfile:
        """Get candidate profile with all details."""
        profile = await self._profile_repo.get_by_id_with_details(candidate_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found.",
            )
        return profile

    async def get_profile_by_resume(
        self, resume_id: uuid.UUID, user_id: uuid.UUID | None = None,
    ) -> CandidateProfile | None:
        """Get a parsed profile linked to one resume, optionally owner-scoped."""
        resume = await self._resume_repo.get_by_id(resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )
        if user_id is not None and resume.candidate_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resume.",
            )
        return await self._profile_repo.get_by_resume_id(resume_id)

    async def get_my_profile(self, user_id: uuid.UUID) -> CandidateProfile | None:
        """Get the current user's candidate profile via their resumes.

        Returns None if no parsed profile exists yet (user hasn't parsed a resume).
        """
        return await self._profile_repo.get_by_user_id(user_id)

    async def list_candidates(
        self, *, skip: int = 0, limit: int = 100,
    ) -> list[CandidateProfile]:
        """Return all candidate profiles."""
        return await self._profile_repo.list_all_with_details(
            skip=skip, limit=limit,
        )

    async def _delete_profile_details(self, profile_id: uuid.UUID) -> None:
        """Remove parsed child rows before rebuilding a profile."""
        for model in (
            CandidateSkill,
            CandidateEducation,
            CandidateExperience,
            CandidateProject,
            CandidateCertification,
        ):
            await self._session.execute(
                delete(model).where(model.candidate_id == profile_id),
            )
