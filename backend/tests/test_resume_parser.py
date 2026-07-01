from pathlib import Path

import pytest

from app.providers.gemini_provider import (
    fallback_parse_resume,
    merge_resume_parse_results,
)
from app.utils.resume_parser import extract_text_from_resume


REAL_RESUME = (
    Path(__file__).parents[1]
    / "uploads"
    / "resumes"
    / "ca48eb9d-5e97-4689-bdb8-8d70b23a7e37"
    / "c2bd9df4fd9346aab4c9abc3c561daca_AJAY KUMAR RESUME1.pdf"
)


@pytest.mark.skipif(not REAL_RESUME.exists(), reason="real resume fixture is not present")
def test_real_resume_extracts_all_recruiting_sections() -> None:
    profile = fallback_parse_resume(extract_text_from_resume(str(REAL_RESUME)))

    assert len(profile["skills"]) >= 15
    assert len(profile["education"]) >= 1
    assert len(profile["projects"]) >= 4
    assert len(profile["achievements"]) >= 4
    assert len(profile["links"]) >= 2
    assert len(profile["research_experience"]) >= 1
    assert not any(
        marker in " ".join(str(value or "") for value in entry.values()).lower()
        for entry in profile["experience"]
        for marker in ("cgpa", "bachelor", "master", "university", "institute", "college")
    )


def test_merge_never_replaces_populated_fallback_sections_with_empty_ai_arrays() -> None:
    fallback = {
        "personal_details": {"full_name": "Candidate"},
        "projects": [{"project_name": "Project A"}],
        "achievements": [{"title": "Achievement A"}],
        "links": [{"url": "https://github.com/example"}],
        "research_experience": [{"title": "Research A"}],
    }
    ai = {
        "personal_details": {"full_name": "Candidate"},
        "projects": [],
        "achievements": [],
        "links": [],
        "research_experience": [],
    }

    merged = merge_resume_parse_results(ai, fallback)

    assert merged["projects"] == fallback["projects"]
    assert merged["achievements"] == fallback["achievements"]
    assert merged["links"] == fallback["links"]
    assert merged["research_experience"] == fallback["research_experience"]
