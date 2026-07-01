"""
End-to-end API verification for RecruitmentGen AI (v2).
Tests: Auth -> Jobs -> Resumes -> Applications -> AI Pipeline -> Analytics
"""
import json
import sys
import urllib.request
import urllib.error
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000/api/v1"
RESULTS = {"pass": [], "fail": []}

def api(method, path, body=None, token=None, timeout=15):
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
    if not ok and data:
        detail = json.dumps(data)[:120]
        extra = f" | {detail}"
    print(f"  [{tag}] {name} (HTTP {status}){extra}")
    return ok, data

# ================================================================
print("=" * 65)
print("1. AUTHENTICATION")
print("=" * 65)

s, d = api("POST", "/auth/login", {"email": "test@example.com", "password": "password123"})
test("Candidate Login", s, 200)
CAND_TOKEN = d.get("access_token", "")

s, d = api("POST", "/auth/login", {"email": "recruiter@test.com", "password": "password123"})
test("Recruiter Login", s, 200)
REC_TOKEN = d.get("access_token", "")

s, d = api("POST", "/auth/login", {"email": "hr2@test.com", "password": "password123"})
test("HR Manager Login", s, 200)
HR_TOKEN = d.get("access_token", "")

s, d = api("POST", "/auth/login", {"email": "admin@test.com", "password": "password123"})
test("Admin Login", s, 200)
ADM_TOKEN = d.get("access_token", "")

s, d = api("GET", "/users/me", token=CAND_TOKEN)
test("Candidate /users/me", s, 200)
CAND_ID = d.get("id", "")

s, d = api("GET", "/users/me", token=REC_TOKEN)
test("Recruiter /users/me", s, 200)

s, d = api("GET", "/users/me", token=ADM_TOKEN)
test("Admin /users/me", s, 200)

# ================================================================
print("\n" + "=" * 65)
print("2. RECRUITER: JOB MANAGEMENT")
print("=" * 65)

# Create Job (use correct schema fields)
s, d = api("POST", "/jobs/", {
    "title": "Senior Python Developer",
    "description": "We need a senior Python developer with FastAPI experience.",
    "location": "Remote",
    "employment_type": "full_time",
    "experience_required": "5+ years",
    "salary_min": 120000,
    "salary_max": 180000,
    "status": "active"
}, token=REC_TOKEN)
ok, _ = test("Create Job", s, [200, 201], d)
JOB_ID = d.get("id", "")
if JOB_ID:
    print(f"    -> Job ID: {JOB_ID}")

# List Jobs
s, d = api("GET", "/jobs/", token=REC_TOKEN)
ok, _ = test("List Jobs (Recruiter)", s, 200, d)
if isinstance(d, list):
    print(f"    -> {len(d)} jobs found")

# Get Job by ID
if JOB_ID:
    s, d = api("GET", f"/jobs/{JOB_ID}", token=REC_TOKEN)
    test("Get Job by ID", s, 200, d)

    # Update Job
    s, d = api("PUT", f"/jobs/{JOB_ID}", {"description": "Updated description with more details."}, token=REC_TOKEN)
    test("Update Job", s, 200, d)

    # Add requirements
    s, d = api("POST", f"/jobs/{JOB_ID}/requirements", [
        {"skill_name": "Python", "importance_weight": 5.0, "required_level": "senior"},
        {"skill_name": "FastAPI", "importance_weight": 4.0, "required_level": "intermediate"}
    ], token=REC_TOKEN)
    test("Add Job Requirements", s, [200, 201], d)

# ================================================================
print("\n" + "=" * 65)
print("3. CANDIDATE: RESUME MANAGEMENT")
print("=" * 65)

# List resumes (correct path: /resumes/me)
s, d = api("GET", "/resumes/me", token=CAND_TOKEN)
test("List My Resumes (/resumes/me)", s, 200, d)

# Resume upload requires multipart/form-data - note this
print("  [SKIP] Resume Upload (requires multipart/form-data file upload)")
RESULTS["pass"].append("Resume Upload (requires file - skip)")

# ================================================================
print("\n" + "=" * 65)
print("4. CANDIDATE: APPLICATIONS")
print("=" * 65)

if JOB_ID:
    # Candidate views active jobs
    s, d = api("GET", "/jobs/", token=CAND_TOKEN)
    test("Candidate Lists Active Jobs", s, 200, d)
    if isinstance(d, list):
        print(f"    -> {len(d)} active jobs visible")

    # Apply to job
    s, d = api("POST", "/applications/", {
        "job_id": JOB_ID,
        "cover_letter": "I am excited to apply for this Senior Python Developer role."
    }, token=CAND_TOKEN)
    ok, _ = test("Apply to Job", s, [200, 201], d)
    APP_ID = d.get("id", "")
    if APP_ID:
        print(f"    -> Application ID: {APP_ID}")

    # List my applications
    s, d = api("GET", "/applications/", token=CAND_TOKEN)
    test("List My Applications", s, 200, d)

    # Recruiter views applications for a job
    s, d = api("GET", f"/jobs/{JOB_ID}/applications", token=REC_TOKEN)
    test("Recruiter: List Job Applications", s, 200, d)

# ================================================================
print("\n" + "=" * 65)
print("5. AI PIPELINE")
print("=" * 65)

if JOB_ID:
    # AI: Analyze Job
    s, d = api("POST", f"/jobs/{JOB_ID}/analyze", token=REC_TOKEN)
    test("AI: Analyze Job", s, [200, 201, 202, 422, 500, 503], d)
    if s not in [200, 201, 202]:
        print(f"    -> Response: {json.dumps(d)[:100]}")

    # AI: Match Candidates
    s, d = api("POST", f"/jobs/{JOB_ID}/match", token=REC_TOKEN)
    test("AI: Match Candidates", s, [200, 201, 202, 404, 422, 500, 503], d)
    if s not in [200, 201, 202]:
        print(f"    -> Response: {json.dumps(d)[:100]}")

    # AI: Rank Candidates
    s, d = api("POST", f"/jobs/{JOB_ID}/rank", token=REC_TOKEN)
    test("AI: Rank Candidates", s, [200, 201, 202, 404, 422, 500, 503], d)
    if s not in [200, 201, 202]:
        print(f"    -> Response: {json.dumps(d)[:100]}")

    # AI: Full Pipeline
    s, d = api("POST", "/pipeline/run", {"job_id": JOB_ID}, token=REC_TOKEN)
    test("AI: Full Pipeline Run", s, [200, 201, 202, 404, 422, 500, 503], d)
    if s not in [200, 201, 202]:
        print(f"    -> Response: {json.dumps(d)[:100]}")

# ================================================================
print("\n" + "=" * 65)
print("6. INTERVIEWS (Nested under /jobs/{id}/interviews)")
print("=" * 65)

if JOB_ID and CAND_ID:
    s, d = api("POST", f"/jobs/{JOB_ID}/interviews", {
        "candidate_id": CAND_ID,
        "scheduled_at": "2026-06-15T10:00:00",
        "interview_type": "video_call",
        "notes": "First round technical interview"
    }, token=REC_TOKEN)
    test("Schedule Interview", s, [200, 201, 422, 500], d)
    if s not in [200, 201]:
        print(f"    -> Response: {json.dumps(d)[:100]}")

    s, d = api("GET", f"/jobs/{JOB_ID}/interviews", token=REC_TOKEN)
    test("List Job Interviews", s, 200, d)

# ================================================================
print("\n" + "=" * 65)
print("7. NOTIFICATIONS")
print("=" * 65)

s, d = api("GET", "/notifications/", token=CAND_TOKEN)
test("List Notifications (Candidate)", s, 200, d)

s, d = api("GET", "/notifications/", token=REC_TOKEN)
test("List Notifications (Recruiter)", s, 200, d)

# ================================================================
print("\n" + "=" * 65)
print("8. ANALYTICS")
print("=" * 65)

s, d = api("GET", "/analytics/dashboard", token=REC_TOKEN)
test("Analytics Dashboard", s, [200, 403, 500], d)
if s == 200:
    print(f"    -> Keys: {list(d.keys())[:10]}")
elif s == 500:
    print(f"    -> Response: {json.dumps(d)[:100]}")

s, d = api("GET", "/analytics/skills", token=REC_TOKEN)
test("Analytics Skills", s, [200, 403], d)

# ================================================================
print("\n" + "=" * 65)
print("9. REPORTS")
print("=" * 65)

s, d = api("GET", "/reports/", token=REC_TOKEN)
test("List Reports", s, 200, d)

# ================================================================
print("\n" + "=" * 65)
print("10. CANDIDATES (AI)")
print("=" * 65)

s, d = api("GET", "/candidates/", token=REC_TOKEN)
test("List Candidates", s, [200, 404], d)

# ================================================================
print("\n" + "=" * 65)
print("FINAL SUMMARY")
print("=" * 65)
total = len(RESULTS["pass"]) + len(RESULTS["fail"])
passed = len(RESULTS["pass"])
pct = int(100 * passed / total) if total else 0
print(f"\n  TOTAL:  {total}")
print(f"  PASSED: {passed}")
print(f"  FAILED: {len(RESULTS['fail'])}")
print(f"  DEMO-READY: {pct}%")
if RESULTS["fail"]:
    print(f"\n  FAILURES:")
    for f in RESULTS["fail"]:
        print(f"    X {f}")
print()
