"""Production validation runner for the live RecruitGen AI stack."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE = "http://localhost:8000/api/v1"
PASSWORD = "Test@12345"
RUN_ID = uuid.uuid4().hex[:8]


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class PersonaResult:
    persona: str
    candidate_email: str
    candidate_id: str = ""
    application_id: str = ""
    job_id: str = ""
    parser_source: str = ""
    stats: dict[str, int] = field(default_factory=dict)
    match_score: float = 0.0
    skill_score: float = 0.0
    evaluation_score: float = 0.0
    recommendation: str = ""
    confidence: float = 0.0
    parse_seconds: float = 0.0
    analyze_seconds: float = 0.0
    match_seconds: float = 0.0
    evaluation_seconds: float = 0.0
    recommendation_seconds: float = 0.0


RESUMES = [
    {
        "persona": "Fresher Resume",
        "name": "Aarav Fresher",
        "headline": "Entry level software engineer with strong academic projects",
        "skills": [
            "Python", "Java", "JavaScript", "HTML", "CSS", "React", "Node.js",
            "SQL", "PostgreSQL", "Git", "REST APIs", "Data Structures",
            "Algorithms", "Linux", "Docker", "Problem Solving",
        ],
        "projects": [
            "Campus Placement Portal | React, Node.js, PostgreSQL | Built student job application workflows.",
            "Library Analytics Dashboard | Python, Pandas, Streamlit | Analyzed book issue patterns.",
            "Expense Tracker | JavaScript, Firebase | Created authentication and reports.",
        ],
        "experience": ["Software Engineering Intern, ByteLabs, Jan 2025 - Apr 2025, Built REST APIs and dashboards."],
        "education": ["B.Tech Computer Science, SRM Institute of Science and Technology, 2021 - 2025, CGPA 8.7"],
        "certifications": ["Python for Everybody, Coursera, 2024", "AWS Cloud Practitioner Essentials, 2024"],
        "job": {
            "title": "Junior Software Engineer",
            "description": "Entry level software engineer with Python, JavaScript, React, Node.js, SQL, PostgreSQL, REST APIs, Git, Docker, data structures and algorithms.",
            "requirements": "Python, JavaScript, React, Node.js, SQL, PostgreSQL, REST APIs, Git, Docker",
        },
    },
    {
        "persona": "Java Developer Resume",
        "name": "Meera Java",
        "headline": "Backend Java developer building enterprise services",
        "skills": [
            "Java", "Spring Boot", "Hibernate", "Microservices", "REST APIs",
            "Kafka", "RabbitMQ", "PostgreSQL", "MySQL", "Redis", "Docker",
            "Kubernetes", "JUnit", "Mockito", "Maven", "Git", "AWS", "CI/CD",
        ],
        "projects": [
            "Order Management Service | Java, Spring Boot, Kafka | Processed order events.",
            "Inventory Sync Platform | Spring Boot, Redis, PostgreSQL | Improved stock reconciliation.",
            "Payment Retry Worker | Java, RabbitMQ | Added fault tolerant retries.",
        ],
        "experience": [
            "Java Developer, FinEdge Systems, 2021 - 2025, Built Spring Boot microservices with Kafka and PostgreSQL.",
            "Backend Intern, SoftWorks, 2020 - 2021, Created REST APIs and JUnit tests.",
        ],
        "education": ["B.E. Information Technology, Pune University, 2016 - 2020"],
        "certifications": ["Oracle Certified Professional Java SE, 2023", "AWS Developer Associate, 2024"],
        "job": {
            "title": "Senior Java Backend Developer",
            "description": "Java backend developer for Spring Boot microservices using Hibernate, Kafka, PostgreSQL, Redis, Docker, Kubernetes, JUnit, AWS and CI/CD.",
            "requirements": "Java, Spring Boot, Hibernate, Microservices, Kafka, PostgreSQL, Redis, Docker, Kubernetes, JUnit",
        },
    },
    {
        "persona": "Data Analyst Resume",
        "name": "Nisha Analyst",
        "headline": "Data analyst specializing in dashboards and decision analytics",
        "skills": [
            "SQL", "Python", "Pandas", "NumPy", "Power BI", "Tableau", "Excel",
            "Statistics", "Data Visualization", "ETL", "Data Modeling", "Snowflake",
            "BigQuery", "Looker", "A/B Testing", "Business Analysis", "Git",
        ],
        "projects": [
            "Sales Intelligence Dashboard | Power BI, SQL | Built executive KPI dashboards.",
            "Customer Churn Analysis | Python, Pandas, Scikit-learn | Identified retention drivers.",
            "Marketing Funnel Report | BigQuery, Looker | Automated campaign reporting.",
        ],
        "experience": [
            "Data Analyst, RetailSense, 2022 - 2025, Built Power BI dashboards and SQL models.",
            "Business Analyst Intern, MarketPulse, 2021 - 2022, Prepared Excel and Tableau reports.",
        ],
        "education": ["B.Sc. Statistics, Delhi University, 2018 - 2021"],
        "certifications": ["Microsoft Power BI Data Analyst, 2023", "Google Data Analytics Certificate, 2022"],
        "job": {
            "title": "Data Analyst",
            "description": "Data analyst with SQL, Python, Pandas, Power BI, Tableau, Excel, statistics, ETL, Snowflake, BigQuery, dashboards and business analysis.",
            "requirements": "SQL, Python, Pandas, Power BI, Tableau, Excel, Statistics, Data Visualization, ETL",
        },
    },
    {
        "persona": "AI/ML Engineer Resume",
        "name": "Rohan ML",
        "headline": "AI/ML engineer building NLP and computer vision systems",
        "skills": [
            "Python", "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy", "OpenCV",
            "Transformers", "Hugging Face", "LangChain", "Vector Database", "RAG",
            "FastAPI", "Docker", "MLflow", "AWS",
        ],
        "projects": [
            "Resume Matching Engine | Python, FastAPI, Transformers | Ranked candidates against job descriptions.",
            "Document Question Answering | LangChain, RAG, Vector Database | Built retrieval augmented answers.",
            "Defect Detection Model | PyTorch, OpenCV | Trained computer vision classifier.",
        ],
        "experience": [
            "ML Engineer, InsightAI, 2021 - 2025, Deployed NLP and computer vision models.",
            "Data Science Intern, VisionLab, 2020 - 2021, Built Scikit-learn pipelines.",
        ],
        "education": ["M.Tech Artificial Intelligence, IIIT Hyderabad, 2018 - 2020"],
        "certifications": ["Deep Learning Specialization, Coursera, 2022", "AWS Machine Learning Specialty, 2024"],
        "job": {
            "title": "AI ML Engineer",
            "description": "AI ML engineer with Python, Machine Learning, Deep Learning, NLP, Computer Vision, PyTorch, TensorFlow, Transformers, LangChain, RAG, Vector Database, FastAPI, Docker and AWS.",
            "requirements": "Python, Machine Learning, Deep Learning, NLP, PyTorch, TensorFlow, Transformers, LangChain, RAG, FastAPI",
        },
    },
    {
        "persona": "Cloud Engineer Resume",
        "name": "Kabir Cloud",
        "headline": "Cloud engineer automating resilient infrastructure",
        "skills": [
            "AWS", "Azure", "Docker", "Kubernetes", "Terraform", "Ansible",
            "Linux", "Networking", "CI/CD", "GitHub Actions", "Jenkins",
            "Prometheus", "Grafana", "Nginx", "EC2", "S3", "RDS", "EKS",
            "Python", "Bash", "Security", "IAM",
        ],
        "projects": [
            "Kubernetes Migration | AWS EKS, Terraform | Migrated services to managed Kubernetes.",
            "Observability Stack | Prometheus, Grafana, Loki | Built production dashboards.",
            "CI/CD Automation | GitHub Actions, Docker | Automated deployments.",
        ],
        "experience": [
            "Cloud Engineer, InfraWorks, 2020 - 2025, Managed AWS, Kubernetes and Terraform infrastructure.",
            "DevOps Intern, CloudOps, 2019 - 2020, Automated Linux server provisioning.",
        ],
        "education": ["B.Tech Electronics and Communication, VIT, 2015 - 2019"],
        "certifications": ["AWS Solutions Architect Associate, 2023", "Certified Kubernetes Administrator, 2024"],
        "job": {
            "title": "Cloud DevOps Engineer",
            "description": "Cloud engineer with AWS, Azure, Docker, Kubernetes, Terraform, Ansible, Linux, CI/CD, GitHub Actions, Jenkins, Prometheus, Grafana, Nginx, EKS, IAM and security.",
            "requirements": "AWS, Docker, Kubernetes, Terraform, Ansible, Linux, CI/CD, Prometheus, Grafana, IAM",
        },
    },
]


def make_resume_pdf(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / f"{RUN_ID}_{data['persona'].replace(' ', '_').replace('/', '_')}.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 48

    def line(text: str, size: int = 10, gap: int = 14) -> None:
        nonlocal y
        if y < 64:
            c.showPage()
            y = height - 48
        c.setFont("Helvetica", size)
        c.drawString(48, y, text[:110])
        y -= gap

    line(data["name"], 16, 20)
    line(f"{data['headline']} | {data['name'].lower().replace(' ', '.')}@validation.test | +91 90000 00000", 9)
    for title, values in (
        ("Technical Skills", [", ".join(data["skills"])]),
        ("Projects", data["projects"]),
        ("Experience", data["experience"]),
        ("Education", data["education"]),
        ("Certifications", data["certifications"]),
        ("Achievements", ["Delivered measurable project outcomes and collaborated with cross-functional teams."]),
    ):
        line(title, 12, 16)
        for value in values:
            line(f"- {value}", 9, 13)
    c.save()
    return path


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    expected: set[int] | None = None,
    **kwargs: Any,
) -> tuple[Any, float, int]:
    expected = expected or {200, 201}
    start = time.perf_counter()
    response = await client.request(method, url, headers=headers, **kwargs)
    elapsed = time.perf_counter() - start
    if response.status_code not in expected:
        raise RuntimeError(f"{method} {url} -> {response.status_code}: {response.text[:500]}")
    if response.content:
        return response.json(), elapsed, response.status_code
    return {}, elapsed, response.status_code


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    data, _, _ = await request_json(client, "POST", "/auth/login", json={"email": email, "password": password})
    return data["access_token"]


async def create_or_login_user(
    client: httpx.AsyncClient,
    admin_headers: dict[str, str],
    *,
    email: str,
    role: str,
    full_name: str,
) -> str:
    payload = {
        "email": email,
        "password": PASSWORD,
        "full_name": full_name,
        "role": role,
        "organization_name": "RecruitGen Validation",
    }
    if role == "candidate":
        response = await client.post("/auth/register", json=payload)
    else:
        response = await client.post("/auth/admin/create-user", json=payload, headers=admin_headers)
    if response.status_code in {200, 201}:
        return response.json()["access_token"]
    if response.status_code == 409 or "already" in response.text.lower():
        return await login(client, email, PASSWORD)
    raise RuntimeError(f"create user {email} failed: {response.status_code}: {response.text[:500]}")


async def main() -> None:
    checks: list[Check] = []
    results: list[PersonaResult] = []
    tmp_dir = Path("/tmp/recruitgen_validation")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(base_url=BASE, timeout=240.0) as client:
        admin_token = await login(client, "admin@recruitgen.ai", "Admin@123456")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        recruiter_token = await create_or_login_user(
            client,
            admin_headers,
            email=f"validation_recruiter_{RUN_ID}@test.com",
            role="recruiter",
            full_name="Validation Recruiter",
        )
        hr_token = await create_or_login_user(
            client,
            admin_headers,
            email=f"validation_hr_{RUN_ID}@test.com",
            role="hr_manager",
            full_name="Validation HR",
        )
        recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        security_cases = [
            ("candidate_create_recruiter_blocked", "/auth/register", {"email": f"bad_recruiter_{RUN_ID}@test.com", "password": PASSWORD, "full_name": "Bad", "role": "recruiter", "organization_name": "BadCo"}, None, {403}),
            ("candidate_create_hr_blocked", "/auth/register", {"email": f"bad_hr_{RUN_ID}@test.com", "password": PASSWORD, "full_name": "Bad", "role": "hr_manager", "organization_name": "BadCo"}, None, {403}),
            ("candidate_create_admin_blocked", "/auth/register", {"email": f"bad_admin_{RUN_ID}@test.com", "password": PASSWORD, "full_name": "Bad", "role": "admin", "organization_name": "BadCo"}, None, {403}),
            ("recruiter_admin_users_blocked", "/users/", None, recruiter_headers, {403}),
            ("hr_admin_users_blocked", "/users/", None, hr_headers, {403}),
        ]
        for name, url, body, headers, expected in security_cases:
            response = await client.request("GET" if body is None else "POST", url, json=body, headers=headers)
            checks.append(Check(name, response.status_code in expected, f"HTTP {response.status_code}"))

        for data in RESUMES:
            email = f"{data['persona'].lower().replace('/', '').replace(' ', '_')}_{RUN_ID}@test.com"
            token = await create_or_login_user(
                client,
                admin_headers,
                email=email,
                role="candidate",
                full_name=data["name"],
            )
            candidate_headers = {"Authorization": f"Bearer {token}"}
            result = PersonaResult(persona=data["persona"], candidate_email=email)

            pdf = make_resume_pdf(data, tmp_dir)
            with pdf.open("rb") as handle:
                upload, _, _ = await request_json(
                    client,
                    "POST",
                    "/resumes/upload",
                    headers=candidate_headers,
                    files={"file": (pdf.name, handle, "application/pdf")},
                )
            parsed, result.parse_seconds, _ = await request_json(
                client,
                "POST",
                f"/resumes/parse/{upload['id']}",
                headers=candidate_headers,
            )
            result.candidate_id = parsed["candidate_id"]
            result.parser_source = parsed["parser_source"]
            result.stats = parsed["statistics"]
            checks.append(Check(
                f"{data['persona']} parse thresholds",
                result.stats.get("skills", 0) > 10
                and result.stats.get("projects", 0) > 1
                and result.stats.get("education", 0) > 0
                and result.stats.get("certifications", 0) > 0
                and result.stats.get("experience", 0) > 0,
                json.dumps(result.stats, sort_keys=True),
            ))

            job_payload = {
                **data["job"],
                "location": "Remote",
                "employment_type": "full_time",
                "experience_level": "mid",
                "status": "active",
            }
            job, _, _ = await request_json(client, "POST", "/jobs/", headers=recruiter_headers, json=job_payload)
            result.job_id = job["id"]
            _, result.analyze_seconds, _ = await request_json(
                client,
                "POST",
                f"/jobs/{result.job_id}/analyze",
                headers=recruiter_headers,
            )
            app, _, _ = await request_json(
                client,
                "POST",
                "/applications/",
                headers=candidate_headers,
                json={"job_id": result.job_id},
                expected={200, 201, 409},
            )
            if isinstance(app, dict):
                result.application_id = app.get("id", "")
            if not result.application_id:
                apps, _, _ = await request_json(client, "GET", "/applications/me", headers=candidate_headers)
                result.application_id = next((item["id"] for item in apps if item["job_id"] == result.job_id), "")

            matches, result.match_seconds, _ = await request_json(
                client,
                "POST",
                f"/jobs/{result.job_id}/match",
                headers=recruiter_headers,
            )
            match = next(item for item in matches["matches"] if item["candidate_id"] == result.candidate_id)
            result.match_score = match["overall_match_score"]
            result.skill_score = match["skill_match_score"]
            checks.append(Check(
                f"{data['persona']} realistic match",
                0 < result.match_score < 1,
                f"overall={result.match_score:.4f}, skill={result.skill_score:.4f}, details={json.dumps(match.get('match_details', {}))[:260]}",
            ))

            evaluation, result.evaluation_seconds, _ = await request_json(
                client,
                "POST",
                f"/jobs/{result.job_id}/evaluate/{result.candidate_id}",
                headers=hr_headers,
            )
            result.evaluation_score = float(evaluation["technical_score"])
            checks.append(Check(
                f"{data['persona']} evaluation non-zero",
                result.evaluation_score > 0,
                f"technical_score={result.evaluation_score}, gaps={len(evaluation.get('skill_gaps') or [])}",
            ))

            recommendation, result.recommendation_seconds, _ = await request_json(
                client,
                "POST",
                f"/jobs/{result.job_id}/recommend/{result.candidate_id}",
                headers=hr_headers,
            )
            result.recommendation = recommendation["decision"]
            result.confidence = float(recommendation["confidence_score"])
            checks.append(Check(
                f"{data['persona']} recommendation confidence",
                result.confidence > 0 and bool(recommendation.get("reasoning")),
                f"decision={result.recommendation}, confidence={result.confidence:.4f}",
            ))
            results.append(result)

        primary = results[0]
        await request_json(client, "PATCH", f"/applications/{primary.application_id}/status", headers=recruiter_headers, json={"status": "screened"})
        await request_json(client, "PATCH", f"/applications/{primary.application_id}/status", headers=recruiter_headers, json={"status": "shortlisted"})
        interview_payload = {
            "candidate_id": primary.candidate_id,
            "job_id": primary.job_id,
            "scheduled_at": "2026-07-01T10:00:00Z",
            "duration_minutes": 30,
            "interview_type": "video",
            "meeting_link": "https://meet.google.com/validation-test",
            "notes": "Production validation interview",
        }
        interview, _, _ = await request_json(client, "POST", f"/jobs/{primary.job_id}/interviews", headers=hr_headers, json=interview_payload)
        await request_json(client, "PATCH", f"/applications/{primary.application_id}/status", headers=hr_headers, json={"status": "interview_scheduled"})
        await request_json(client, "PATCH", f"/interviews/{interview['id']}", headers=hr_headers, json={"status": "completed", "feedback": "Strong validation candidate"})
        await request_json(client, "PATCH", f"/applications/{primary.application_id}/status", headers=hr_headers, json={"status": "interview_completed"})
        await request_json(client, "PATCH", f"/applications/{primary.application_id}/status", headers=hr_headers, json={"status": "selected"})
        offer_start = time.perf_counter()
        offer, _, _ = await request_json(client, "POST", f"/offers/{primary.application_id}/generate", headers=hr_headers)
        offer_seconds = time.perf_counter() - offer_start
        offer_download = await client.get(f"/offers/{primary.application_id}/download", headers={"Authorization": f"Bearer {admin_token}"})
        checks.append(Check("offer generated and downloadable", offer_download.status_code == 200 and len(offer_download.content) > 1000, f"generate_seconds={offer_seconds:.2f}, bytes={len(offer_download.content)}"))

        reports: dict[str, Any] = {}
        for report_type, payload in {
            "hiring": {"report_type": "hiring", "title": "Validation Hiring Report"},
            "analytics": {"report_type": "analytics", "title": "Validation Analytics Report"},
            "match": None,
        }.items():
            start = time.perf_counter()
            if report_type == "match":
                report, _, _ = await request_json(client, "POST", f"/reports/match/{primary.job_id}", headers=admin_headers)
            else:
                report, _, _ = await request_json(client, "POST", "/reports/", headers=admin_headers, json=payload)
            reports[report_type] = {"id": report["id"], "seconds": time.perf_counter() - start}
            for suffix in ("download", "excel", "csv"):
                export = await client.get(f"/reports/{report['id']}/{suffix}", headers=admin_headers)
                checks.append(Check(f"{report_type} report {suffix}", export.status_code == 200 and len(export.content) > 100, f"bytes={len(export.content)}"))

        notifications, _, _ = await request_json(client, "GET", "/notifications/", headers=admin_headers)
        analytics, _, _ = await request_json(client, "GET", "/analytics/dashboard", headers=admin_headers)
        ai_status, _, _ = await request_json(client, "GET", "/ai/status", headers=admin_headers)

    summary = {
        "run_id": RUN_ID,
        "checks": [check.__dict__ for check in checks],
        "personas": [result.__dict__ for result in results],
        "reports": reports,
        "notifications_seen": len(notifications.get("notifications", notifications) if isinstance(notifications, dict) else notifications),
        "analytics_stats": analytics.get("stats", {}),
        "ai_status": ai_status,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
