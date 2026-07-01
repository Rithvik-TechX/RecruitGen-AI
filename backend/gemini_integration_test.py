"""
Gemini AI Integration Verification — Standalone Test
=====================================================
Tests all 6 integration points directly (no Docker required):
  1. GEMINI_API_KEY loads from .env
  2. GeminiProvider class
  3. Resume parsing
  4. JD analysis
  5. Hiring recommendation
  6. Skill evaluation
"""

import asyncio
import json
import os
import sys
import io
import time
import traceback

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Make sure we can import the app modules ──────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# Load .env manually first for a pre-check
from dotenv import load_dotenv, find_dotenv

RESULTS = {"pass": [], "fail": [], "skip": []}
DIVIDER = "=" * 65


def record(name: str, passed: bool, detail: str = ""):
    tag = "PASS" if passed else "FAIL"
    bucket = "pass" if passed else "fail"
    RESULTS[bucket].append(name)
    suffix = f"\n    → {detail}" if detail else ""
    print(f"  [{tag}] {name}{suffix}")
    return passed


def header(step: int, title: str):
    print(f"\n{DIVIDER}")
    print(f"  STEP {step}: {title}")
    print(DIVIDER)


# ================================================================
# STEP 1: Verify GEMINI_API_KEY loads from .env
# ================================================================
header(1, "Verify GEMINI_API_KEY loads from .env")

# 1a — Raw dotenv load
env_path = find_dotenv(usecwd=True)
if not env_path:
    # Try parent directory
    env_path = os.path.join(os.path.dirname(os.getcwd()), ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.getcwd(), "..", ".env")

load_dotenv(env_path)
raw_key = os.environ.get("GEMINI_API_KEY", "")
record(
    "1a. .env file found",
    os.path.exists(env_path),
    f"Path: {env_path}",
)
record(
    "1b. GEMINI_API_KEY present in environment",
    bool(raw_key),
    f"Key length: {len(raw_key)} chars, starts with: {raw_key[:8]}..." if raw_key else "MISSING",
)

# 1c — Pydantic Settings load
try:
    from app.core.config import Settings, get_settings
    # Clear the lru_cache so it re-reads
    get_settings.cache_clear()
    settings = get_settings()
    key_from_settings = settings.GEMINI_API_KEY
    record(
        "1c. Settings.GEMINI_API_KEY loaded via pydantic-settings",
        bool(key_from_settings),
        f"Model: {settings.GEMINI_MODEL}, Key length: {len(key_from_settings)}",
    )
except Exception as exc:
    record("1c. Settings.GEMINI_API_KEY loaded via pydantic-settings", False, str(exc))

# ================================================================
# STEP 2: Test GeminiProvider
# ================================================================
header(2, "Test GeminiProvider")

try:
    from app.providers.gemini_provider import GeminiProvider, get_gemini_client

    # 2a — Client instantiation
    client = get_gemini_client()
    record("2a. get_gemini_client() returns a client", client is not None, type(client).__name__)

    # 2b — GeminiProvider instantiation
    provider = GeminiProvider()
    record("2b. GeminiProvider() instantiates", provider is not None)

    # 2c — Simple generation test
    async def test_provider_generate():
        result = await provider.generate("Respond with exactly: HELLO_GEMINI_OK")
        return result

    gen_result = asyncio.run(test_provider_generate())
    has_response = bool(gen_result and len(gen_result.strip()) > 0)
    record(
        "2c. GeminiProvider.generate() returns text",
        has_response,
        f"Response length: {len(gen_result)} chars" if gen_result else "Empty response",
    )

except Exception as exc:
    record("2. GeminiProvider tests", False, f"{type(exc).__name__}: {exc}")
    traceback.print_exc()

# ================================================================
# STEP 3: Test Resume Parsing
# ================================================================
header(3, "Test Resume Parsing (parse_resume_with_gemini)")

SAMPLE_RESUME = """
RITHVIK SHARMA
Email: rithvik.sharma@email.com | Phone: +91 98765 43210
LinkedIn: linkedin.com/in/rithviksharma | GitHub: github.com/rithvik

SUMMARY
Full Stack Developer with 4+ years of experience building scalable web applications
using React.js, Node.js, and Python. Passionate about clean code and DevOps practices.

SKILLS
- Languages: Python, JavaScript, TypeScript, Java, SQL
- Frontend: React.js, Next.js, Redux, Tailwind CSS, HTML5/CSS3
- Backend: Node.js, Express.js, FastAPI, Django
- Databases: PostgreSQL, MongoDB, Redis
- Cloud/DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, CI/CD, GitHub Actions
- Tools: Git, Jira, Figma, VS Code

EXPERIENCE
Senior Full Stack Developer | TechCorp India | Bangalore
Jan 2022 – Present
- Led development of a microservices platform serving 50K+ users
- Built React.js dashboards with real-time data visualization
- Designed RESTful APIs using FastAPI and PostgreSQL
- Implemented CI/CD pipelines reducing deployment time by 60%
Technologies: React, FastAPI, PostgreSQL, Docker, AWS

Software Developer | StartupXYZ | Hyderabad
Jun 2020 – Dec 2021
- Developed full-stack features for an e-commerce platform
- Built payment integration using Stripe API
- Optimized database queries improving response times by 40%
Technologies: Node.js, React, MongoDB, Express.js

EDUCATION
B.Tech in Computer Science | IIT Hyderabad | 2016 – 2020 | GPA: 8.7/10

PROJECTS
- CloudDeploy: Automated cloud deployment tool using Python and AWS SDK
- TaskFlow: Project management app built with Next.js and MongoDB

CERTIFICATIONS
- AWS Certified Solutions Architect – Associate (2023)
- Google Cloud Professional Data Engineer (2022)
"""

try:
    from app.providers.gemini_provider import parse_resume_with_gemini

    async def test_resume_parsing():
        return await parse_resume_with_gemini(SAMPLE_RESUME)

    t0 = time.time()
    parsed = asyncio.run(test_resume_parsing())
    elapsed = time.time() - t0

    # Validate structure
    record(
        "3a. parse_resume_with_gemini returns dict",
        isinstance(parsed, dict),
        f"Keys: {list(parsed.keys())} (took {elapsed:.1f}s)",
    )

    personal = parsed.get("personal_details", {})
    record(
        "3b. Personal details extracted",
        bool(personal.get("full_name")),
        f"Name: {personal.get('full_name')}, Email: {personal.get('email')}",
    )

    skills = parsed.get("skills", [])
    record(
        "3c. Skills extracted",
        len(skills) >= 5,
        f"{len(skills)} skills found. First 5: {[s.get('skill_name') for s in skills[:5]]}",
    )

    experience = parsed.get("experience", [])
    record(
        "3d. Experience extracted",
        len(experience) >= 2,
        f"{len(experience)} entries. Companies: {[e.get('company') for e in experience]}",
    )

    education = parsed.get("education", [])
    record(
        "3e. Education extracted",
        len(education) >= 1,
        f"{len(education)} entries. Institutions: {[e.get('institution') for e in education]}",
    )

    certs = parsed.get("certifications", [])
    record(
        "3f. Certifications extracted",
        len(certs) >= 1,
        f"{len(certs)} certifications found",
    )

except Exception as exc:
    record("3. Resume parsing", False, f"{type(exc).__name__}: {exc}")
    traceback.print_exc()

# ================================================================
# STEP 4: Test JD Analysis
# ================================================================
header(4, "Test JD Analysis (analyze_jd_with_gemini)")

SAMPLE_JD = """
Full Stack Engineer — TechCorp India (Bangalore)

We are looking for a Full Stack Engineer to join our growing team.

Requirements:
- 3+ years of experience with React.js and Node.js
- Strong understanding of TypeScript, REST APIs, and GraphQL
- Experience with PostgreSQL or MongoDB databases
- Familiarity with Docker and CI/CD pipelines
- Experience with AWS or GCP cloud services
- Strong problem-solving skills and attention to detail

Responsibilities:
- Design and implement frontend and backend features
- Write clean, maintainable, and well-tested code
- Participate in code reviews and architectural discussions
- Collaborate with product and design teams
- Deploy and monitor applications in production

Nice to have:
- Experience with Next.js or Remix
- Knowledge of microservices architecture
- Experience with Redis or message queues
- Open source contributions
"""

try:
    from app.providers.gemini_provider import analyze_jd_with_gemini

    async def test_jd_analysis():
        return await analyze_jd_with_gemini(SAMPLE_JD)

    t0 = time.time()
    jd_result = asyncio.run(test_jd_analysis())
    elapsed = time.time() - t0

    record(
        "4a. analyze_jd_with_gemini returns dict",
        isinstance(jd_result, dict),
        f"Keys: {list(jd_result.keys())} (took {elapsed:.1f}s)",
    )

    req_skills = jd_result.get("required_skills", [])
    record(
        "4b. Required skills extracted",
        len(req_skills) >= 3,
        f"{len(req_skills)} required skills. Top: {[s.get('name') for s in req_skills[:5]]}",
    )

    pref_skills = jd_result.get("preferred_skills", [])
    record(
        "4c. Preferred skills extracted",
        len(pref_skills) >= 1,
        f"{len(pref_skills)} preferred skills. Top: {[s.get('name') for s in pref_skills[:3]]}",
    )

    # Check weights are assigned
    has_weights = all(isinstance(s.get("weight"), (int, float)) for s in req_skills[:3])
    record(
        "4d. Skill weights assigned (0.0-1.0)",
        has_weights,
        f"Sample weights: {[s.get('weight') for s in req_skills[:5]]}",
    )

    keywords = jd_result.get("keywords", [])
    record(
        "4e. Keywords extracted",
        len(keywords) >= 3,
        f"{len(keywords)} keywords: {keywords[:6]}",
    )

    summary = jd_result.get("analysis_summary", "")
    record(
        "4f. Analysis summary generated",
        len(summary) > 20,
        f"Summary: {summary[:120]}...",
    )

except Exception as exc:
    record("4. JD analysis", False, f"{type(exc).__name__}: {exc}")
    traceback.print_exc()

# ================================================================
# STEP 5: Test Hiring Recommendation (Gemini prompt)
# ================================================================
header(5, "Test Hiring Recommendation (GeminiProvider)")

try:
    provider = GeminiProvider()

    hiring_context = {
        "candidate_name": "Rithvik Sharma",
        "candidate_summary": "Full Stack Developer with 4+ years experience",
        "skills": ["Python", "React.js", "Node.js", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience_count": 2,
        "education": [{"degree": "B.Tech CS", "institution": "IIT Hyderabad"}],
        "match_scores": {"overall": 85.0, "skill": 90.0, "experience": 80.0, "education": 75.0},
        "skill_evaluation": {
            "technical_score": 88.0,
            "strengths": ["React", "FastAPI", "Docker"],
            "skill_gaps": [{"skill": "GraphQL", "importance": "nice_to_have"}],
        },
        "job_requirements": {
            "required_skills": [
                {"name": "React.js", "weight": 0.9},
                {"name": "Node.js", "weight": 0.8},
                {"name": "TypeScript", "weight": 0.8},
            ],
            "experience": {"minimum_years": 3},
        },
    }

    hiring_prompt = f"""You are a senior HR AI advisor. Based on all available data, produce a hiring recommendation.

CANDIDATE & EVALUATION DATA:
{json.dumps(hiring_context, indent=2)}

Respond with ONLY valid JSON (no markdown):
{{
    "decision": "hire" | "consider" | "reject",
    "confidence_score": <float 0.0-1.0>,
    "risk_assessment": "<assessment of hiring risks>",
    "strengths": [
        {{"area": "<area>", "detail": "<explanation>"}}
    ],
    "weaknesses": [
        {{"area": "<area>", "detail": "<explanation>"}}
    ],
    "reasoning": "<detailed reasoning for the decision>",
    "summary": "<one-sentence recommendation>"
}}"""

    async def test_hiring_rec():
        return await provider.generate(hiring_prompt)

    t0 = time.time()
    raw_response = asyncio.run(test_hiring_rec())
    elapsed = time.time() - t0

    # Parse the response
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
    hiring_result = json.loads(cleaned)

    record(
        "5a. Hiring recommendation returns valid JSON",
        isinstance(hiring_result, dict),
        f"Took {elapsed:.1f}s",
    )

    decision = hiring_result.get("decision", "")
    record(
        "5b. Decision field present (hire/consider/reject)",
        decision in ("hire", "consider", "reject"),
        f"Decision: {decision}",
    )

    confidence = hiring_result.get("confidence_score", -1)
    record(
        "5c. Confidence score in range [0.0, 1.0]",
        0.0 <= confidence <= 1.0,
        f"Confidence: {confidence}",
    )

    record(
        "5d. Risk assessment present",
        bool(hiring_result.get("risk_assessment")),
        f"Risk: {str(hiring_result.get('risk_assessment', ''))[:100]}",
    )

    record(
        "5e. Reasoning present",
        bool(hiring_result.get("reasoning")),
        f"Reasoning: {str(hiring_result.get('reasoning', ''))[:100]}...",
    )

    record(
        "5f. Strengths/weaknesses populated",
        len(hiring_result.get("strengths", [])) > 0,
        f"Strengths: {len(hiring_result.get('strengths', []))}, "
        f"Weaknesses: {len(hiring_result.get('weaknesses', []))}",
    )

except Exception as exc:
    record("5. Hiring recommendation", False, f"{type(exc).__name__}: {exc}")
    traceback.print_exc()

# ================================================================
# STEP 6: Test Skill Evaluation (Gemini prompt)
# ================================================================
header(6, "Test Skill Evaluation (GeminiProvider)")

try:
    provider = GeminiProvider()

    candidate_skills = [
        {"name": "Python", "level": "expert", "years": 4, "category": "programming_language"},
        {"name": "React.js", "level": "advanced", "years": 3, "category": "framework"},
        {"name": "PostgreSQL", "level": "advanced", "years": 3, "category": "database"},
        {"name": "Docker", "level": "intermediate", "years": 2, "category": "devops"},
        {"name": "AWS", "level": "intermediate", "years": 2, "category": "cloud"},
    ]

    candidate_experience = [
        {
            "company": "TechCorp India",
            "title": "Senior Full Stack Developer",
            "description": "Led microservices platform development, built React dashboards, designed REST APIs",
            "technologies": "React, FastAPI, PostgreSQL, Docker, AWS",
        },
        {
            "company": "StartupXYZ",
            "title": "Software Developer",
            "description": "Full-stack e-commerce features, payment integration, query optimization",
            "technologies": "Node.js, React, MongoDB, Express.js",
        },
    ]

    job_requirements = {
        "required_skills": [
            {"name": "React.js", "weight": 0.9, "is_required": True},
            {"name": "Node.js", "weight": 0.8, "is_required": True},
            {"name": "TypeScript", "weight": 0.8, "is_required": True},
            {"name": "PostgreSQL", "weight": 0.7, "is_required": True},
        ],
        "preferred_skills": [
            {"name": "Next.js", "weight": 0.5, "is_required": False},
            {"name": "Redis", "weight": 0.4, "is_required": False},
        ],
        "experience_requirements": {"minimum_years": 3, "preferred_years": 5},
    }

    skill_eval_prompt = f"""You are a technical recruiter AI. Evaluate the candidate's skills against the job requirements.

CANDIDATE SKILLS:
{json.dumps(candidate_skills, indent=2)}

CANDIDATE EXPERIENCE:
{json.dumps(candidate_experience, indent=2)}

JOB REQUIREMENTS:
{json.dumps(job_requirements, indent=2)}

Respond with ONLY valid JSON (no markdown):
{{
    "technical_score": <float 0-100>,
    "competency_scores": {{
        "programming": <float 0-100>,
        "frameworks": <float 0-100>,
        "databases": <float 0-100>,
        "cloud_devops": <float 0-100>,
        "soft_skills": <float 0-100>,
        "domain_knowledge": <float 0-100>
    }},
    "skill_gaps": [
        {{"skill": "<name>", "importance": "critical|important|nice_to_have", "suggestion": "<learning path>"}}
    ],
    "strengths": ["<strength 1>", "<strength 2>"],
    "evaluation_summary": "<2-3 sentence overall assessment>"
}}"""

    async def test_skill_eval():
        return await provider.generate(skill_eval_prompt)

    t0 = time.time()
    raw_response = asyncio.run(test_skill_eval())
    elapsed = time.time() - t0

    # Parse the response
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
    eval_result = json.loads(cleaned)

    record(
        "6a. Skill evaluation returns valid JSON",
        isinstance(eval_result, dict),
        f"Took {elapsed:.1f}s",
    )

    tech_score = eval_result.get("technical_score", -1)
    record(
        "6b. Technical score in range [0, 100]",
        0 <= tech_score <= 100,
        f"Score: {tech_score}",
    )

    comp_scores = eval_result.get("competency_scores", {})
    record(
        "6c. Competency scores populated",
        len(comp_scores) >= 4,
        f"Categories: {list(comp_scores.keys())}",
    )

    gaps = eval_result.get("skill_gaps", [])
    record(
        "6d. Skill gaps identified",
        isinstance(gaps, list),
        f"{len(gaps)} gaps: {[g.get('skill') for g in gaps[:5]]}",
    )

    strengths = eval_result.get("strengths", [])
    record(
        "6e. Strengths identified",
        len(strengths) >= 1,
        f"{len(strengths)} strengths: {strengths[:3]}",
    )

    summary = eval_result.get("evaluation_summary", "")
    record(
        "6f. Evaluation summary generated",
        len(summary) > 20,
        f"Summary: {summary[:120]}...",
    )

except Exception as exc:
    record("6. Skill evaluation", False, f"{type(exc).__name__}: {exc}")
    traceback.print_exc()


# ================================================================
# FINAL SUMMARY
# ================================================================
print(f"\n{DIVIDER}")
print("  GEMINI INTEGRATION VERIFICATION — FINAL RESULTS")
print(DIVIDER)

total = len(RESULTS["pass"]) + len(RESULTS["fail"])
passed = len(RESULTS["pass"])
failed = len(RESULTS["fail"])
pct = int(100 * passed / total) if total else 0

print(f"""
  TOTAL:  {total}
  PASSED: {passed}  ✓
  FAILED: {failed}  ✗
  RATE:   {pct}%
""")

if RESULTS["fail"]:
    print("  FAILURES:")
    for f in RESULTS["fail"]:
        print(f"    ✗ {f}")
    print()

if pct == 100:
    print("  🎉 ALL GEMINI INTEGRATION TESTS PASSED!")
elif pct >= 80:
    print("  ⚠  MOSTLY PASSING — review failures above.")
else:
    print("  ❌ SIGNIFICANT FAILURES — Gemini integration needs attention.")

print()
sys.exit(0 if failed == 0 else 1)
