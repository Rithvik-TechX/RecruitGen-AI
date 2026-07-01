"""
Embedding Provider — text embeddings via Sentence Transformers.

Model: BAAI/bge-small-en-v1.5  (384-dimensional, normalised).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import structlog
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """Return a lazily-loaded embedding model singleton."""
    global _model
    if _model is None:
        settings = get_settings()
        logger.info("loading_embedding_model", model=settings.EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("embedding_model_loaded")
    return _model


# ── Core Embedding Functions ────────────────────────────────


def generate_embedding(text: str) -> list[float]:
    """Generate a normalised embedding for a single text."""
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate normalised embeddings for a batch of texts."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()


# ── Text Builders ───────────────────────────────────────────


def build_candidate_text(profile_data: dict[str, Any]) -> str:
    """Build a comprehensive text representation of a candidate profile."""
    parts: list[str] = []

    if profile_data.get("full_name"):
        parts.append(f"Name: {profile_data['full_name']}")
    if profile_data.get("summary"):
        parts.append(f"Summary: {profile_data['summary']}")

    # Skills
    skills = profile_data.get("skills", [])
    if skills:
        names = [s.get("skill_name", "") for s in skills if s.get("skill_name")]
        if names:
            parts.append(f"Skills: {', '.join(names)}")

    # Experience
    for exp in profile_data.get("experiences", []):
        tokens: list[str] = []
        if exp.get("title"):
            tokens.append(exp["title"])
        if exp.get("company"):
            tokens.append(f"at {exp['company']}")
        if exp.get("description"):
            tokens.append(f"- {exp['description']}")
        if exp.get("technologies"):
            tokens.append(f"Technologies: {exp['technologies']}")
        if tokens:
            parts.append("Experience: " + " ".join(tokens))

    # Education
    for edu in profile_data.get("educations", []):
        tokens = []
        if edu.get("degree"):
            tokens.append(edu["degree"])
        if edu.get("field_of_study"):
            tokens.append(f"in {edu['field_of_study']}")
        if edu.get("institution"):
            tokens.append(f"from {edu['institution']}")
        if tokens:
            parts.append("Education: " + " ".join(tokens))

    # Projects
    for proj in profile_data.get("projects", []):
        tokens = []
        if proj.get("project_name"):
            tokens.append(proj["project_name"])
        if proj.get("description"):
            tokens.append(f"- {proj['description']}")
        if proj.get("technologies"):
            tokens.append(f"Technologies: {proj['technologies']}")
        if tokens:
            parts.append("Project: " + " ".join(tokens))

    # Certifications
    for cert in profile_data.get("certifications", []):
        tokens = []
        if cert.get("certification_name"):
            tokens.append(cert["certification_name"])
        if cert.get("issuing_organization"):
            tokens.append(f"by {cert['issuing_organization']}")
        if tokens:
            parts.append("Certification: " + " ".join(tokens))

    for achievement in profile_data.get("achievements", []):
        title = achievement.get("title")
        description = achievement.get("description")
        if title:
            parts.append(f"Achievement: {title}" + (f" - {description}" if description else ""))

    for internship in profile_data.get("internships", []):
        role = internship.get("role", "")
        company = internship.get("company", "")
        description = internship.get("description")
        text = f"Internship: {role} at {company}".strip()
        parts.append(text + (f" - {description}" if description else ""))

    for award in profile_data.get("awards", []):
        if award.get("title"):
            parts.append(f"Award: {award['title']}")

    for publication in profile_data.get("publications", []):
        if publication.get("title"):
            parts.append(f"Publication: {publication['title']}")

    languages = profile_data.get("languages", [])
    if languages:
        parts.append(f"Languages: {', '.join(languages)}")

    return "\n".join(parts)


def build_job_text(
    job_data: dict[str, Any],
    analysis_data: dict[str, Any] | None = None,
) -> str:
    """Build a comprehensive text representation of a job posting."""
    parts: list[str] = []

    if job_data.get("title"):
        parts.append(f"Job Title: {job_data['title']}")
    if job_data.get("description"):
        parts.append(f"Description: {job_data['description']}")
    if job_data.get("requirements"):
        parts.append(f"Requirements: {job_data['requirements']}")
    if job_data.get("responsibilities"):
        parts.append(f"Responsibilities: {job_data['responsibilities']}")

    if analysis_data:
        required = analysis_data.get("required_skills", [])
        if required:
            names = [s.get("name", "") for s in required if s.get("name")]
            if names:
                parts.append(f"Required Skills: {', '.join(names)}")

        preferred = analysis_data.get("preferred_skills", [])
        if preferred:
            names = [s.get("name", "") for s in preferred if s.get("name")]
            if names:
                parts.append(f"Preferred Skills: {', '.join(names)}")

        keywords = analysis_data.get("keywords", [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")

    return "\n".join(parts)


# ── Similarity ──────────────────────────────────────────────


def compute_cosine_similarity(
    embedding1: list[float], embedding2: list[float],
) -> float:
    """Compute cosine similarity between two embeddings."""
    a = np.array(embedding1)
    b = np.array(embedding2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
