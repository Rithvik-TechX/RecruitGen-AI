"""
Gemini AI Provider — resume parsing & JD analysis.

Handles all interactions with the Google Gemini API using
the ``google-genai`` SDK.
"""

from __future__ import annotations

import json
import asyncio
import re
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any, TypeVar

import structlog
from google import genai
from google.genai import types

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

# ── Client singleton ────────────────────────────────────────

_client: genai.Client | None = None
MAX_GEMINI_ATTEMPTS = 3
GEMINI_REQUEST_TIMEOUT_SECONDS = 90
AI_STATUS: dict[str, Any] = {
    "state": "ACTIVE",
    "last_success_at": None,
    "last_failure_at": None,
    "last_error": None,
}
T = TypeVar("T")


class GeminiServiceError(RuntimeError):
    """Structured Gemini failure that can be mapped to an HTTP status."""

    def __init__(self, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def _is_retryable_gemini_error(exc: Exception) -> bool:
    """Return true for transient Gemini/service-capacity failures."""
    message = str(exc).lower()
    return any(
        marker in message
        for marker in ("503", "unavailable", "temporarily", "high demand", "rate limit", "timeout", "timed out")
    )


def _gemini_error_status(exc: Exception) -> int:
    """Map Gemini SDK errors to client-meaningful HTTP status codes."""
    message = str(exc).lower()
    if "429" in message or "quota" in message or "rate limit" in message:
        return 429
    if "503" in message or "unavailable" in message or "high demand" in message:
        return 503
    return 502


def _gemini_error_message(status_code: int) -> str:
    if status_code == 429:
        return "Quota exceeded. Please try again after your Gemini quota resets."
    if status_code == 503:
        return "AI service unavailable. Please try again later."
    return "AI service failed to process the request."


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_ai_success() -> None:
    AI_STATUS.update({
        "state": "ACTIVE",
        "last_success_at": _utc_now_iso(),
        "last_error": None,
    })


def mark_ai_failure(exc: Exception | str, *, fallback_available: bool = True) -> None:
    AI_STATUS.update({
        "state": "FALLBACK" if fallback_available else "UNAVAILABLE",
        "last_failure_at": _utc_now_iso(),
        "last_error": str(exc),
    })


def get_ai_status() -> dict[str, Any]:
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        return {
            **AI_STATUS,
            "state": "UNAVAILABLE",
            "provider": "gemini",
            "model": settings.GEMINI_MODEL,
            "message": "Gemini API key is not configured.",
        }
    state = AI_STATUS["state"]
    message = {
        "ACTIVE": "Gemini Active",
        "FALLBACK": "Fallback Mode",
        "UNAVAILABLE": "AI Unavailable",
    }.get(state, "AI status unknown")
    return {
        **AI_STATUS,
        "provider": "gemini",
        "model": settings.GEMINI_MODEL,
        "message": message,
    }


async def _generate_content_with_retry(
    *,
    model: str,
    contents: str,
    config: types.GenerateContentConfig,
    response_parser: Callable[[str], T] | None = None,
) -> str | T:
    """Call Gemini with bounded retries for transient service failures."""
    client = get_gemini_client()
    last_exc: Exception | None = None

    for attempt in range(1, MAX_GEMINI_ATTEMPTS + 1):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=config,
                ),
                timeout=GEMINI_REQUEST_TIMEOUT_SECONDS,
            )
            response_text = response.text or ""
            mark_ai_success()
            return response_parser(response_text) if response_parser else response_text
        except Exception as exc:
            last_exc = exc
            mark_ai_failure(exc)
            if attempt == MAX_GEMINI_ATTEMPTS:
                raise
            delay = 2 ** (attempt - 1)
            logger.warning(
                "gemini_retrying_after_parse_failure",
                attempt=attempt,
                delay_seconds=delay,
                timeout_seconds=GEMINI_REQUEST_TIMEOUT_SECONDS,
                error=str(exc),
            )
            await asyncio.sleep(delay)

    raise RuntimeError(f"Gemini generation failed: {last_exc}")


def get_gemini_client() -> genai.Client:
    """Return a lazily-initialised Gemini client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


# ── GeminiProvider class ────────────────────────────────────


class GeminiProvider:
    """Wrapper class for Gemini AI interactions.

    Used by SkillEvaluationService and HiringRecommendationService
    for free-form prompt generation.
    """

    def __init__(self) -> None:
        self._client = get_gemini_client()
        self._settings = get_settings()

    async def generate(self, prompt: str) -> str:
        """Generate text from a prompt using Gemini."""
        try:
            result = await _generate_content_with_retry(
                model=self._settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8192,
                ),
            )
            return str(result)
        except Exception as exc:
            logger.error("gemini_generate_error", error=str(exc))
            status_code = _gemini_error_status(exc)
            raise GeminiServiceError(
                _gemini_error_message(status_code),
                status_code=status_code,
            ) from exc


# ── Prompts ─────────────────────────────────────────────────

RESUME_PARSE_PROMPT = """You are an expert resume parser. Analyze the following resume text and extract structured data.

Return a JSON object with EXACTLY this structure (no markdown, no code blocks, just raw JSON):
{
    "personal_details": {
        "full_name": "string or null",
        "email": "string or null",
        "phone": "string or null",
        "linkedin_url": "string or null",
        "github_url": "string or null",
        "summary": "string or null"
    },
    "skills": [
        {
            "skill_name": "string",
            "proficiency_level": "expert|advanced|intermediate|beginner|null",
            "category": "programming_language|framework|database|cloud|devops|tool|soft_skill|other"
        }
    ],
    "education": [
        {
            "institution": "string",
            "degree": "string or null",
            "field_of_study": "string or null",
            "start_date": "string or null",
            "end_date": "string or null",
            "gpa": "string or null",
            "description": "string or null"
        }
    ],
    "experience": [
        {
            "company": "string",
            "title": "string",
            "location": "string or null",
            "start_date": "string or null",
            "end_date": "string or null",
            "is_current": false,
            "description": "string or null",
            "technologies": "comma-separated string or null"
        }
    ],
    "projects": [
        {
            "project_name": "string",
            "description": "string or null",
            "technologies": ["string"],
            "year": "string or null",
            "url": "string or null",
            "start_date": "string or null",
            "end_date": "string or null"
        }
    ],
    "certifications": [
        {
            "certification_name": "string",
            "issuing_organization": "string or null",
            "issue_date": "string or null",
            "expiry_date": "string or null",
            "credential_id": "string or null",
            "credential_url": "string or null"
        }
    ],
    "achievements": [
        {
            "title": "string",
            "description": "string or null",
            "date": "string or null"
        }
    ],
    "internships": [
        {
            "company": "string",
            "role": "string",
            "duration": "string or null",
            "start_date": "string or null",
            "end_date": "string or null",
            "description": "string or null",
            "technologies": ["string"]
        }
    ],
    "awards": [
        {
            "title": "string",
            "issuer": "string or null",
            "date": "string or null",
            "description": "string or null"
        }
    ],
    "publications": [
        {
            "title": "string",
            "publisher": "string or null",
            "publication_date": "string or null",
            "url": "string or null",
            "description": "string or null"
        }
    ],
    "research_experience": [
        {
            "title": "string",
            "description": "string or null",
            "duration": "string or null"
        }
    ],
    "languages": ["string"],
    "links": [
        {
            "link_type": "github|linkedin|portfolio|website|kaggle|leetcode|codechef|hackerrank|other",
            "label": "string or null",
            "url": "string"
        }
    ]
}

RULES:
- Extract ALL skills mentioned anywhere in the resume including in experience descriptions
- Categorize each skill appropriately
- For dates, preserve the original format from the resume
- If a field cannot be determined, use null
- For current positions, set is_current to true and end_date to null
- Keep internships separate from full-time experience
- Keep research exposure and research experience separate from work experience
- Never classify education records as work experience
- Extract every project, certification, achievement, award, publication, research entry, language, and profile link
- Treat Achievements & Competitive Programming as achievements
- Treat Research Exposure and Research Experience as research_experience
- Preserve link URLs exactly as written
- Return ONLY valid JSON, no other text

RESUME TEXT:
"""

JD_ANALYSIS_PROMPT = """You are an expert job description analyzer. Analyze the following job description and extract structured requirements.

Return a JSON object with EXACTLY this structure (no markdown, no code blocks, just raw JSON):
{
    "required_skills": [
        {
            "name": "string",
            "weight": 0.0,
            "is_required": true
        }
    ],
    "preferred_skills": [
        {
            "name": "string",
            "weight": 0.0,
            "is_required": false
        }
    ],
    "education_requirements": {
        "minimum_degree": "string or null",
        "preferred_degree": "string or null",
        "preferred_fields": ["string"],
        "is_degree_required": false
    },
    "experience_requirements": {
        "minimum_years": 0,
        "preferred_years": 0,
        "required_titles": ["string"],
        "preferred_industries": ["string"]
    },
    "keywords": ["string"],
    "analysis_summary": "string"
}

RULES:
- Assign weights (0.0 to 1.0) based on emphasis in the JD
- Must-have skills get higher weights (0.7-1.0)
- Nice-to-have skills get lower weights (0.3-0.6)
- Extract ALL technical and soft skills mentioned
- Keywords should include industry terms, technologies, methodologies
- Return ONLY valid JSON, no other text

JOB DESCRIPTION:
"""


def _clean_json_response(text: str) -> str:
    """Strip markdown code-fence wrappers if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)
    return text


COMMON_SKILLS = [
    # Programming Languages
    "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go",
    "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R", "MATLAB",
    "Perl", "Shell", "Bash", "PowerShell", "Dart", "Lua", "Haskell",
    "Elixir", "Clojure", "Groovy", "Objective-C", "Visual Basic", "Assembly",
    "COBOL", "Fortran", "Julia", "Solidity", "VHDL", "Verilog",
    # Web Frontend
    "React", "Next.js", "Angular", "Vue.js", "Svelte", "jQuery", "Bootstrap",
    "Tailwind CSS", "HTML", "CSS", "SASS", "LESS", "Webpack", "Vite",
    "Redux", "MobX", "Zustand", "Material UI", "Ant Design", "Chakra UI",
    "Styled Components", "Storybook", "Three.js", "D3.js", "WebGL", "WebSocket",
    # Web Backend
    "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot",
    "ASP.NET", "Ruby on Rails", "Laravel", "NestJS", "Gin", "Fiber",
    "GraphQL", "REST", "gRPC", "Celery", "RabbitMQ", "Redis", "Kafka",
    "Apache Spark", "Nginx", "Apache", "Gunicorn", "Uvicorn",
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Oracle", "SQL Server",
    "Cassandra", "DynamoDB", "Firebase", "Firestore", "Neo4j",
    "Elasticsearch", "InfluxDB", "CockroachDB", "MariaDB", "Supabase",
    "PlanetScale", "Prisma", "SQLAlchemy", "Sequelize", "Mongoose", "TypeORM",
    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Travis CI",
    "ArgoCD", "Helm", "Prometheus", "Grafana", "ELK Stack", "Datadog",
    "New Relic", "Vault", "Consul", "Istio", "Pulumi", "CloudFormation",
    "Serverless", "Lambda", "EC2", "S3", "RDS", "EKS", "ECS", "Fargate",
    # AI/ML/Data Science
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
    "SciPy", "Matplotlib", "Seaborn", "Jupyter", "OpenCV", "Hugging Face",
    "LangChain", "LLM", "GPT", "BERT", "Transformers", "NLTK", "SpaCy",
    "XGBoost", "LightGBM", "CatBoost", "MLflow", "DVC",
    "Weights & Biases", "Data Analysis", "Data Engineering", "Data Pipeline",
    "Feature Engineering", "Model Deployment", "MLOps", "Neural Networks",
    "AI",
    # Data Engineering & Analytics
    "Hadoop", "Hive", "Presto", "Airflow", "dbt", "Snowflake", "BigQuery",
    "Redshift", "Databricks", "ETL", "Data Warehouse", "Data Lake",
    "Power BI", "Tableau", "Looker", "Metabase", "Data Visualization",
    "SQL", "NoSQL", "Data Modeling", "Apache Kafka", "Apache Flink",
    "Apache Beam",
    # Mobile
    "React Native", "Flutter", "SwiftUI", "Jetpack Compose", "iOS",
    "Android", "Xcode", "Android Studio", "Expo", "Capacitor", "Ionic",
    "Cordova",
    # Testing
    "Jest", "Mocha", "Pytest", "JUnit", "Selenium", "Cypress", "Playwright",
    "TestNG", "PHPUnit", "RSpec", "Postman", "K6", "Locust", "TestCafe",
    "Vitest", "Testing Library", "Enzyme",
    # Security
    "OAuth", "JWT", "SAML", "SSL/TLS", "OWASP", "Penetration Testing",
    "Encryption", "IAM", "Cybersecurity", "SOC", "SIEM", "Firewall", "VPN",
    "PKI", "Zero Trust",
    # Project/Tools
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Slack",
    "Trello", "Notion", "Figma", "VS Code", "IntelliJ", "Eclipse", "Vim",
    "Linux", "Unix", "Windows Server", "macOS", "Agile", "Scrum", "Kanban",
    "CI/CD", "DevOps", "SRE", "Microservices", "Monolith", "Event-Driven",
    "CQRS", "Clean Architecture", "Design Patterns", "System Design",
    "API Design",
    # Business/Soft Skills
    "Communication", "Leadership", "Problem Solving", "Critical Thinking",
    "Teamwork", "Project Management", "Time Management",
    "Stakeholder Management", "Requirements Analysis", "Technical Writing",
    "Documentation", "Mentoring", "Presentation", "Negotiation",
    "Strategic Planning", "Business Analysis", "Product Management",
    "UX Design",
    # Emerging Tech
    "Blockchain", "Web3", "IoT", "AR/VR", "5G", "Edge Computing",
    "Quantum Computing", "Robotics", "3D Printing", "Digital Twin",
    "Generative AI", "Prompt Engineering", "RAG", "Vector Database",
    "ChromaDB", "Pinecone", "Weaviate",
    # ERP/Enterprise
    "SAP", "Salesforce", "ServiceNow", "Oracle ERP", "Workday", "HubSpot",
    "Zendesk", "Dynamics 365", "SharePoint", "Power Automate",
]

SECTION_ALIASES = {
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
        "major projects",
        "research projects",
    },
    "certifications": {"certifications", "certificates", "training", "courses"},
    "achievements": {
        "achievements",
        "accomplishments",
        "recognition",
        "competitive programming",
        "achievements competitive programming",
    },
    "awards": {"awards", "honors", "honours"},
    "internships": {"internship", "internships", "industrial training"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "research_experience": {
        "research exposure",
        "research experience",
        "research work",
        "research exposure self directed learning",
    },
    "publications": {"publications", "papers"},
    "languages": {"languages", "language proficiency"},
    "links": {"links", "profiles", "profile links", "coding profiles", "social profiles"},
    "skills": {
        "skills",
        "technical skills",
        "core competencies",
        "programming skills",
        "technologies",
        "tools",
        "tech stack",
        "tools and technologies",
        "technical proficiency",
        "tools technologies",
        "technical expertise",
    },
}
ALL_SECTION_HEADINGS = {
    heading: section
    for section, headings in SECTION_ALIASES.items()
    for heading in headings
}
RESUME_SECTION_HEADINGS = set(ALL_SECTION_HEADINGS) | {
    "summary",
    "objective",
    "profile",
    "contact",
    "contact information",
    "skills",
    "technical skills",
    "education",
    "academic background",
    "technical skills language skills and interests",
    "core competencies",
    "research interest",
    "references",
    "interests",
    "hobbies",
}


def _normalise_heading(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", line.lower())).strip()


def _clean_resume_item(line: str) -> str:
    return re.sub(r"^[\s•●▪◦\-–—*]+", "", line).strip()


def _match_section_heading(line: str) -> tuple[bool, str | None]:
    heading = _normalise_heading(line)
    if not heading or len(heading.split()) > 8:
        return False, None
    if heading in RESUME_SECTION_HEADINGS:
        return True, ALL_SECTION_HEADINGS.get(heading)

    matches = [
        (alias, section)
        for alias, section in ALL_SECTION_HEADINGS.items()
        if heading.startswith(f"{alias} ") or heading.endswith(f" {alias}")
    ]
    if matches:
        _, section = max(matches, key=lambda item: len(item[0]))
        return True, section

    stop_prefixes = (
        "summary",
        "objective",
        "technical skills",
        "skills",
        "education",
        "core competencies",
        "interests",
        "references",
    )
    if heading.startswith(stop_prefixes):
        return True, None
    return False, None


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections = {name: [] for name in SECTION_ALIASES}
    current: str | None = None
    for line in lines:
        is_heading, section = _match_section_heading(line)
        if is_heading:
            current = section
            continue
        if current:
            sections[current].append(line)
    return sections


def _extract_urls(resume_text: str) -> list[dict[str, str | None]]:
    pattern = re.compile(
        r"(?:https?://|www\.)[^\s,;]+|"
        r"(?:github\.com|linkedin\.com/in|kaggle\.com|leetcode\.com|"
        r"codechef\.com|hackerrank\.com)/[^\s,;]+",
        re.IGNORECASE,
    )
    links: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for match in pattern.findall(resume_text):
        url = match.rstrip(").]")
        if not url.lower().startswith(("http://", "https://")):
            url = f"https://{url}"
        if url.lower() in seen:
            continue
        seen.add(url.lower())
        lowered = url.lower()
        link_type = next(
            (
                name
                for name in (
                    "github",
                    "linkedin",
                    "kaggle",
                    "leetcode",
                    "codechef",
                    "hackerrank",
                )
                if name in lowered
            ),
            "portfolio" if "portfolio" in lowered else "website",
        )
        links.append({"link_type": link_type, "label": link_type.title(), "url": url})
    return links


def _extract_year(text: str) -> str | None:
    match = re.search(r"\b(?:19|20)\d{2}\b", text)
    return match.group(0) if match else None


def _extract_technologies(text: str) -> list[str]:
    lowered = text.lower()
    return [skill for skill in COMMON_SKILLS if skill.lower() in lowered]


def _extract_skills_from_section(lines: list[str]) -> list[dict[str, Any]]:
    """Extract skills directly from the resume's skills section text."""
    skills: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in lines:
        cleaned = _clean_resume_item(line)
        if not cleaned:
            continue
        if ':' in cleaned:
            category, _, items = cleaned.partition(':')
            category = category.strip()
            for item in re.split(r'[,;|•●▪◦]', items):
                name = item.strip().rstrip('.')
                if name and len(name) > 1 and len(name) < 60 and name.lower() not in seen:
                    seen.add(name.lower())
                    skills.append({"skill_name": name, "proficiency_level": None, "category": category.lower()})
        else:
            for item in re.split(r'[,;|•●▪◦]', cleaned):
                name = item.strip().rstrip('.')
                if name and len(name) > 1 and len(name) < 60 and name.lower() not in seen:
                    seen.add(name.lower())
                    skills.append({"skill_name": name, "proficiency_level": None, "category": "other"})
    return skills


def _section_entries(
    lines: list[str],
    *,
    bullets_are_entries: bool = False,
) -> list[tuple[str, str | None]]:
    entries: list[tuple[str, str | None]] = []
    current_title: str | None = None
    descriptions: list[str] = []

    def flush() -> None:
        nonlocal current_title, descriptions
        if current_title:
            entries.append((current_title, " ".join(descriptions) or None))
        current_title = None
        descriptions = []

    for raw_line in lines:
        clean = _clean_resume_item(raw_line)
        if not clean:
            continue
        is_bullet = raw_line.lstrip().startswith(("-", "•", "●", "▪", "◦", "*"))
        if is_bullet and current_title and not bullets_are_entries:
            descriptions.append(clean)
            continue
        flush()
        separator = re.search(r":(?!//)", clean)
        if separator:
            title = clean[:separator.start()]
            description = clean[separator.end():]
            current_title = title.strip()
            descriptions = [description.strip()] if description.strip() else []
        else:
            current_title = clean
    flush()
    return entries


def _clean_structured_item(line: str) -> str:
    return re.sub(r"^[\s•●▪◦\-–—*]+", "", line).strip()


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[•●▪◦\-–—*]\s*", line))


def _extract_project_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Extract all projects from a bounded project section."""
    projects: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current
        if current and current["project_name"]:
            description_parts = current.pop("_description_parts")
            current["description"] = " ".join(description_parts).strip() or None
            combined = f"{current['project_name']} {current['description'] or ''}"
            current["technologies"] = list(dict.fromkeys(
                current["technologies"] + _extract_technologies(combined)
            ))
            projects.append(current)
        current = None

    def start_project(clean: str) -> None:
        nonlocal current
        title, separator, remainder = clean.partition("|")
        technologies: list[str] = []
        description_parts: list[str] = []
        if separator:
            tech_text, second_separator, description = remainder.partition("|")
            technologies = [
                item.strip()
                for item in re.split(r"[,;/]", tech_text)
                if item.strip()
            ]
            if second_separator and description.strip():
                description_parts.append(description.strip())
        current = {
            "project_name": title.strip()[:255],
            "technologies": technologies,
            "year": _extract_year(clean),
            "url": None,
            "start_date": None,
            "end_date": None,
            "_description_parts": description_parts,
        }

    for index, raw_line in enumerate(lines):
        clean = _clean_structured_item(raw_line)
        if not clean:
            continue
        next_line = _clean_structured_item(lines[index + 1]) if index + 1 < len(lines) else ""
        is_year_line = bool(re.fullmatch(r"(?:19|20)\d{2}", clean))
        starts_project = (
            "|" in clean
            or (
                not _is_bullet(raw_line)
                and (
                    current is None
                    or (
                        bool(re.fullmatch(r"(?:19|20)\d{2}", next_line))
                        and not _extract_year(clean)
                    )
                )
            )
        )

        if starts_project:
            flush()
            start_project(clean)
            continue
        if current is None:
            continue
        if is_year_line and not current["year"]:
            current["year"] = clean
            continue
        current["_description_parts"].append(clean)

    flush()
    return projects


def _extract_achievement_entries(lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        combined = " ".join(current).strip()
        parts = re.split(r"\s+[—–-]\s+", combined, maxsplit=1)
        entries.append({
            "title": parts[0][:500],
            "description": parts[1] if len(parts) > 1 else None,
            "date": _extract_year(combined),
        })
        current = []

    for raw_line in lines:
        clean = _clean_structured_item(raw_line)
        if not clean:
            continue
        if _is_bullet(raw_line):
            flush()
        current.append(clean)
    flush()
    return entries


def _extract_research_entries(lines: list[str]) -> list[dict[str, str | None]]:
    clean_lines = [_clean_structured_item(line) for line in lines]
    clean_lines = [line for line in clean_lines if line]
    if not clean_lines:
        return []
    duration_pattern = re.compile(
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*(?:19|20)\d{2}"
        r"\s*(?:-|–|—|to)\s*"
        r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*(?:19|20)\d{2}|Present|Current)",
        re.IGNORECASE,
    )
    duration = next(
        (match.group(0) for line in clean_lines if (match := duration_pattern.search(line))),
        None,
    )
    description_lines = [
        line
        for line in clean_lines[1:]
        if line != duration and line.lower() not in {"online", "remote", "self-directed", "virtual"}
    ]
    return [{
        "title": clean_lines[0][:500],
        "description": " ".join(description_lines).strip() or None,
        "duration": duration,
    }]


EDUCATION_MARKERS = (
    "cgpa",
    "bachelor",
    "master",
    "university",
    "institute",
    "college",
    "b.tech",
    "m.tech",
    "mtech",
    "btech",
    "b.e",
    "m.e",
    "b.sc",
    "m.sc",
    "degree",
)


def _clean_experience_sections(parsed: dict[str, Any]) -> dict[str, Any]:
    """Prevent AI or fallback output from mixing education/research into work."""
    cleaned_experience: list[dict[str, Any]] = []
    research = list(parsed.get("research_experience") or [])
    for item in parsed.get("experience") or []:
        if not isinstance(item, dict):
            continue
        combined = " ".join(str(value or "") for value in item.values()).lower()
        if any(marker in combined for marker in EDUCATION_MARKERS):
            continue
        if "research" in combined or "self-directed" in combined:
            research.append({
                "title": item.get("title") or item.get("company") or "Research Experience",
                "description": item.get("description"),
                "duration": " - ".join(
                    str(value)
                    for value in (item.get("start_date"), item.get("end_date"))
                    if value
                ) or None,
            })
            continue
        cleaned_experience.append(item)
    parsed["experience"] = cleaned_experience
    parsed["research_experience"] = research
    return parsed


def fallback_parse_resume(resume_text: str) -> dict[str, Any]:
    """Section-aware local parser used when Gemini is unavailable."""
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    sections = _extract_sections(lines)
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", resume_text)
    full_name = next(
        (
            line
            for line in lines[:10]
            if "@" not in line and not any(char.isdigit() for char in line) and len(line.split()) <= 5
        ),
        "Candidate",
    )

    lowered = resume_text.lower()
    links = _extract_urls(resume_text)
    skills_section_lines = sections.get("skills", []) or []
    section_skills = _extract_skills_from_section(skills_section_lines)

    common_matched = [
        {
            "skill_name": skill,
            "proficiency_level": None,
            "category": "other",
        }
        for skill in COMMON_SKILLS
        if skill.lower() in lowered
    ]

    seen_skills: set[str] = set()
    skills: list[dict[str, Any]] = []
    for s in section_skills + common_matched:
        key = s["skill_name"].lower()
        if key not in seen_skills:
            seen_skills.add(key)
            skills.append(s)

    education = [
        {
            "institution": line[:255],
            "degree": None,
            "field_of_study": None,
            "start_date": None,
            "end_date": None,
            "gpa": None,
            "description": None,
        }
        for line in lines
        if any(
            token in line.lower()
            for token in (
                "university",
                "college",
                "institute",
                "bachelor",
                "master",
                "b.tech",
                "m.tech",
                "btech",
                "mtech",
                "b.e",
                "m.e",
                "b.sc",
                "m.sc",
                "degree",
            )
        )
    ][:3]

    experience_lines = sections["experience"] if any(sections.values()) else lines
    experience = [
        {
            "company": "Not specified",
            "title": line[:255],
            "location": None,
            "start_date": None,
            "end_date": None,
            "is_current": False,
            "description": line,
            "technologies": ", ".join(s["skill_name"] for s in skills[:8]) or None,
        }
        for line in experience_lines
        if any(token in line.lower() for token in ("engineer", "developer", "intern", "analyst", "manager", "consultant"))
    ][:3]

    projects = _extract_project_entries(sections["projects"])

    certifications = []
    for title, description in _section_entries(
        sections["certifications"],
        bullets_are_entries=True,
    ):
        combined = f"{title} {description or ''}"
        parts = [part.strip() for part in re.split(r"\s+[|–—-]\s+|,\s*", combined) if part.strip()]
        certifications.append({
            "certification_name": parts[0][:255],
            "issuing_organization": parts[1][:255] if len(parts) > 1 and not _extract_year(parts[1]) else None,
            "issue_date": _extract_year(combined),
            "expiry_date": None,
            "credential_id": None,
            "credential_url": None,
        })

    achievements = _extract_achievement_entries(sections["achievements"])
    awards = []
    for title, description in _section_entries(
        sections["awards"],
        bullets_are_entries=True,
    ):
        combined = f"{title} {description or ''}"
        parts = [part.strip() for part in re.split(r"\s+[|–—-]\s+", title) if part.strip()]
        awards.append({
            "title": parts[0][:500],
            "issuer": parts[1][:255] if len(parts) > 1 and not _extract_year(parts[1]) else None,
            "date": _extract_year(combined),
            "description": description,
        })

    internships = []
    for title, description in _section_entries(sections["internships"]):
        combined = f"{title} {description or ''}"
        parts = [part.strip() for part in re.split(r"\s+[|–—-]\s+", title) if part.strip()]
        duration_match = re.search(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*\d{4})"
            r"\s*(?:-|–|—|to)\s*"
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*\d{4}|Present|Current)",
            combined,
            re.IGNORECASE,
        )
        internships.append({
            "company": parts[1][:255] if len(parts) > 1 else "Not specified",
            "role": parts[0][:255],
            "duration": " - ".join(duration_match.groups()) if duration_match else None,
            "start_date": None,
            "end_date": None,
            "description": description,
            "technologies": _extract_technologies(combined),
        })

    publications = []
    for title, description in _section_entries(
        sections["publications"],
        bullets_are_entries=True,
    ):
        combined = f"{title} {description or ''}"
        parts = [part.strip() for part in re.split(r"\s+[|–—-]\s+", title) if part.strip()]
        publications.append({
            "title": parts[0][:500],
            "publisher": parts[1][:255] if len(parts) > 1 and not _extract_year(parts[1]) else None,
            "publication_date": _extract_year(combined),
            "url": next((link["url"] for link in links if link["url"] and link["url"] in combined), None),
            "description": description,
        })
    languages = [
        language.strip()
        for line in sections["languages"]
        for language in re.split(r"[,|•]", _clean_resume_item(line))
        if language.strip()
    ]

    if not skills:
        skills = [{"skill_name": "Communication", "proficiency_level": None, "category": "soft_skill"}]

    linkedin = next((link["url"] for link in links if link["link_type"] == "linkedin"), None)
    github = next((link["url"] for link in links if link["link_type"] == "github"), None)
    research_experience = _extract_research_entries(sections["research_experience"])

    return _clean_experience_sections({
        "personal_details": {
            "full_name": full_name,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0).strip() if phone_match else None,
            "linkedin_url": linkedin,
            "github_url": github,
            "summary": "Profile generated using local parsing because the AI service was unavailable.",
        },
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "internships": internships,
        "awards": awards,
        "publications": publications,
        "research_experience": research_experience,
        "languages": languages,
        "links": links,
    })


def merge_resume_parse_results(
    ai_result: dict[str, Any],
    fallback_result: dict[str, Any],
) -> dict[str, Any]:
    """Keep AI output primary while filling omitted sections locally."""
    merged = dict(ai_result)
    ai_personal = ai_result.get("personal_details") or {}
    fallback_personal = fallback_result.get("personal_details") or {}
    merged["personal_details"] = {
        key: ai_personal.get(key) or fallback_personal.get(key)
        for key in set(ai_personal) | set(fallback_personal)
    }

    identity_keys = {
        "skills": ("skill_name",),
        "education": ("institution", "degree"),
        "experience": ("company", "title"),
        "projects": ("project_name", "title"),
        "certifications": ("certification_name",),
        "achievements": ("title",),
        "internships": ("company", "role"),
        "awards": ("title",),
        "publications": ("title",),
        "research_experience": ("title",),
        "links": ("url",),
    }
    for section, keys in identity_keys.items():
        ai_items = ai_result.get(section) or []
        fallback_items = fallback_result.get(section) or []
        # Combine both sources and deduplicate
        combined: list[Any] = []
        seen: set[tuple[str, ...]] = set()
        for item in ai_items + fallback_items:
            if not isinstance(item, dict):
                continue
            identity = tuple(
                str(item.get(key) or "").strip().lower()
                for key in keys
            )
            if not any(identity) or identity in seen:
                continue
            seen.add(identity)
            combined.append(item)
        merged[section] = combined

    merged["languages"] = list(dict.fromkeys(
        str(language).strip()
        for language in (ai_result.get("languages") or []) + (fallback_result.get("languages") or [])
        if str(language).strip()
    ))
    return _clean_experience_sections(merged)


def fallback_analyze_jd(job_description: str) -> dict[str, Any]:
    """Best-effort local JD analysis used only when Gemini is unavailable."""
    lowered = job_description.lower()
    matched_skills = [skill for skill in COMMON_SKILLS if skill.lower() in lowered]
    required_skills = [
        {"name": skill, "weight": 0.8, "is_required": True}
        for skill in matched_skills[:12]
    ]
    if not required_skills:
        required_skills = [{"name": "Communication", "weight": 0.5, "is_required": True}]

    years_match = re.search(r"(\d+)\+?\s*(?:years|yrs)", lowered)
    years = int(years_match.group(1)) if years_match else 0

    return {
        "required_skills": required_skills,
        "preferred_skills": [],
        "education_requirements": {
            "minimum_degree": None,
            "preferred_degree": None,
            "preferred_fields": [],
            "is_degree_required": False,
        },
        "experience_requirements": {
            "minimum_years": years,
            "preferred_years": years,
            "required_titles": [],
            "preferred_industries": [],
        },
        "keywords": matched_skills[:12],
        "analysis_summary": "Analysis generated using local parsing because the AI service was unavailable.",
    }


# ── Public API ──────────────────────────────────────────────


async def parse_resume_with_gemini(resume_text: str) -> dict[str, Any]:
    """Parse resume text using Gemini AI and return structured data."""
    settings = get_settings()

    try:
        parsed = await _generate_content_with_retry(
            model=settings.GEMINI_MODEL,
            contents=RESUME_PARSE_PROMPT + resume_text,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=16384,
                response_mime_type="application/json",
            ),
            response_parser=lambda text: json.loads(_clean_json_response(text)),
        )
        logger.info("resume_parsed_with_gemini")
        return parsed

    except json.JSONDecodeError as exc:
        logger.error("gemini_resume_invalid_json", error=str(exc))
        raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc
    except Exception as exc:
        logger.error("gemini_resume_api_error", error=str(exc))
        status_code = _gemini_error_status(exc)
        raise GeminiServiceError(
            _gemini_error_message(status_code),
            status_code=status_code,
        ) from exc


async def analyze_jd_with_gemini(job_description: str) -> dict[str, Any]:
    """Analyze a job description using Gemini AI and return structured requirements."""
    settings = get_settings()

    try:
        parsed = await _generate_content_with_retry(
            model=settings.GEMINI_MODEL,
            contents=JD_ANALYSIS_PROMPT + job_description,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
            ),
            response_parser=lambda text: json.loads(_clean_json_response(text)),
        )
        logger.info("jd_analyzed_with_gemini")
        return parsed

    except json.JSONDecodeError as exc:
        logger.error("gemini_jd_invalid_json", error=str(exc))
        raise ValueError(f"Gemini returned invalid JSON for JD: {exc}") from exc
    except Exception as exc:
        logger.error("gemini_jd_api_error", error=str(exc))
        status_code = _gemini_error_status(exc)
        raise GeminiServiceError(
            _gemini_error_message(status_code),
            status_code=status_code,
        ) from exc
