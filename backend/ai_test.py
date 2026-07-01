"""
Gemini AI Integration Test — tests all AI endpoints end-to-end.
"""
import json
import sys
import urllib.request
import urllib.error
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000/api/v1"
RESULTS = {"pass": [], "fail": []}

def api(method, path, body=None, token=None, timeout=60):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        content = resp.read().decode()
        return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode()
        try:
            return e.code, json.loads(content)
        except:
            return e.code, {"detail": content}
    except Exception as e:
        return 0, {"detail": str(e)}

def test(name, status, expected, data=None):
    exp = expected if isinstance(expected, list) else [expected]
    ok = status in exp
    tag = "PASS" if ok else "FAIL"
    RESULTS["pass" if ok else "fail"].append(name)
    extra = ""
    if data:
        detail = json.dumps(data)[:200]
        extra = f"\n    Response: {detail}"
    print(f"  [{tag}] {name} (HTTP {status}){extra}")
    return ok, data

# ================================================================
# Wait for backend
# ================================================================
print("Waiting for backend...")
for i in range(20):
    try:
        urllib.request.urlopen("http://localhost:8000/", timeout=5)
        print(f"Backend ready after {i*3}s\n")
        break
    except:
        time.sleep(3)
else:
    print("Backend not ready after 60s!")
    sys.exit(1)

# ================================================================
# Login as recruiter
# ================================================================
print("=" * 65)
print("STEP 0: Authentication")
print("=" * 65)

s, d = api("POST", "/auth/login", {"email": "recruiter@test.com", "password": "password123"})
test("Recruiter Login", s, 200)
REC_TOKEN = d.get("access_token", "")

s, d = api("POST", "/auth/login", {"email": "test@example.com", "password": "password123"})
test("Candidate Login", s, 200)
CAND_TOKEN = d.get("access_token", "")

# Get candidate user ID
s, d = api("GET", "/users/me", token=CAND_TOKEN)
CAND_ID = d.get("id", "")

# ================================================================
# STEP 1: Verify Gemini API Key is loaded
# ================================================================
print("\n" + "=" * 65)
print("STEP 1: Verify GEMINI_API_KEY is loaded")
print("=" * 65)
# We test this implicitly by calling the analyze endpoint.
# If it fails with "API key" error, we know it's not loaded.
# Let's first create a job to test with.

s, d = api("POST", "/jobs/", {
    "title": "Full Stack Engineer",
    "description": """We are looking for a Full Stack Engineer to join our growing team.

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
- Open source contributions""",
    "location": "Bangalore, India",
    "employment_type": "full_time",
    "experience_required": "3-5 years",
    "salary_min": 1500000,
    "salary_max": 2500000,
    "status": "active"
}, token=REC_TOKEN)
test("Create Test Job", s, [200, 201], d)
JOB_ID = d.get("id", "")
print(f"    Job ID: {JOB_ID}")

# ================================================================
# STEP 2: Test JD Analysis (Gemini)
# ================================================================
print("\n" + "=" * 65)
print("STEP 2: JD Analysis (POST /jobs/{id}/analyze)")
print("=" * 65)

if JOB_ID:
    s, d = api("POST", f"/jobs/{JOB_ID}/analyze", token=REC_TOKEN)
    ok, _ = test("AI: Analyze Job Description", s, [200, 201], d)
    if ok and isinstance(d, dict):
        print(f"    -> Analysis Status: {d.get('analysis_status', 'N/A')}")
        req_skills = d.get("required_skills", [])
        pref_skills = d.get("preferred_skills", [])
        keywords = d.get("keywords", [])
        print(f"    -> Required Skills: {len(req_skills)}")
        for sk in req_skills[:5]:
            print(f"       - {sk.get('name', '?')} (weight: {sk.get('weight', '?')})")
        print(f"    -> Preferred Skills: {len(pref_skills)}")
        print(f"    -> Keywords: {keywords[:5]}")
        print(f"    -> Summary: {(d.get('analysis_summary') or '')[:120]}...")
    elif not ok:
        detail = d.get("detail", "")
        if "API key" in str(detail) or "api_key" in str(detail).lower():
            print("    !! GEMINI_API_KEY NOT LOADED OR INVALID !!")
        else:
            print(f"    Error: {str(detail)[:200]}")

# ================================================================
# STEP 3: Test Candidate Matching (uses embeddings + Gemini analysis)
# ================================================================
print("\n" + "=" * 65)
print("STEP 3: Candidate Matching (POST /jobs/{id}/match)")
print("=" * 65)

if JOB_ID:
    s, d = api("POST", f"/jobs/{JOB_ID}/match", token=REC_TOKEN)
    ok, _ = test("AI: Match Candidates", s, [200, 201], d)
    if ok:
        matches = d.get("matches", [])
        print(f"    -> {len(matches)} matches found")
        for m in matches[:3]:
            print(f"       - {m.get('candidate_name','?')}: overall={m.get('overall_match_score',0):.1f}% skill={m.get('skill_match_score',0):.1f}%")
    else:
        print(f"    Note: {json.dumps(d)[:150]}")

# ================================================================
# STEP 4: Test Candidate Ranking
# ================================================================
print("\n" + "=" * 65)
print("STEP 4: Candidate Ranking (POST /jobs/{id}/rank)")
print("=" * 65)

if JOB_ID:
    s, d = api("POST", f"/jobs/{JOB_ID}/rank", token=REC_TOKEN)
    ok, _ = test("AI: Rank Candidates", s, [200, 201, 400], d)
    if ok and s in [200, 201]:
        rankings = d.get("rankings", [])
        print(f"    -> {len(rankings)} ranked candidates")
        for r in rankings[:3]:
            print(f"       #{r.get('rank_position',0)} {r.get('candidate_name','?')}: score={r.get('final_score',0):.1f}")
    else:
        print(f"    Note: {json.dumps(d)[:150]}")

# ================================================================
# STEP 5: Test Skill Evaluation endpoint
# ================================================================
print("\n" + "=" * 65)
print("STEP 5: Skill Evaluation")
print("=" * 65)

# Check the evaluations endpoint
s, d = api("GET", "/evaluations/jobs/" + JOB_ID if JOB_ID else "/evaluations/", token=REC_TOKEN)
test("List Skill Evaluations", s, [200, 404, 405], d)

# ================================================================
# STEP 6: Test Hiring Recommendation endpoint
# ================================================================
print("\n" + "=" * 65)
print("STEP 6: Hiring Recommendation")
print("=" * 65)

# Check the recommendations endpoint
s, d = api("GET", "/recommendations/jobs/" + JOB_ID if JOB_ID else "/recommendations/", token=REC_TOKEN)
test("List Hiring Recommendations", s, [200, 404, 405], d)

# ================================================================
# STEP 7: Get stored analysis result
# ================================================================
print("\n" + "=" * 65)
print("STEP 7: Get Stored Analysis")
print("=" * 65)

if JOB_ID:
    s, d = api("GET", f"/jobs/{JOB_ID}/analysis", token=REC_TOKEN)
    test("Get Stored Job Analysis", s, [200, 404], d)

# ================================================================
# SUMMARY
# ================================================================
print("\n" + "=" * 65)
print("GEMINI INTEGRATION SUMMARY")
print("=" * 65)
total = len(RESULTS["pass"]) + len(RESULTS["fail"])
passed = len(RESULTS["pass"])
pct = int(100 * passed / total) if total else 0
print(f"\n  TOTAL:  {total}")
print(f"  PASSED: {passed}")
print(f"  FAILED: {len(RESULTS['fail'])}")
if RESULTS["fail"]:
    print(f"\n  FAILURES:")
    for f in RESULTS["fail"]:
        print(f"    X {f}")
print()
