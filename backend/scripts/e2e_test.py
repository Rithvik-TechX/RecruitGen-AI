"""
Full E2E Workflow Test Script for RecruitGen AI.

Runs inside Docker: docker compose exec backend python -m scripts.e2e_test
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

BASE = "http://localhost:8000/api/v1"
RESULTS = []

def log(test: str, passed: bool, detail: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    RESULTS.append((test, passed, detail))
    print(f"  {status} | {test}" + (f" - {detail}" if detail else ""))

async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30.0) as c:
        print("\n" + "="*60)
        print("  RECRUITGEN AI - E2E WORKFLOW TEST")
        print("="*60)

        # -- 1. SECURITY TEST: Block non-candidate registration --
        print("\n-- SECURITY TESTS --")
        r = await c.post("/auth/register", json={
            "email": "hacker@test.com", "password": "Test@12345",
            "full_name": "Hacker", "role": "recruiter",
            "organization_name": "Evil Corp"
        })
        log("Block recruiter registration", r.status_code == 403,
            f"HTTP {r.status_code}")

        r = await c.post("/auth/register", json={
            "email": "hacker2@test.com", "password": "Test@12345",
            "full_name": "Hacker2", "role": "hr_manager",
            "organization_name": "Evil Corp"
        })
        log("Block HR registration", r.status_code == 403,
            f"HTTP {r.status_code}")

        r = await c.post("/auth/register", json={
            "email": "hacker3@test.com", "password": "Test@12345",
            "full_name": "Hacker3", "role": "admin",
            "organization_name": "Evil Corp"
        })
        log("Block admin registration", r.status_code == 403,
            f"HTTP {r.status_code}")

        # ── 2. Login as existing admin ──
        print("\n-- AUTH TESTS --")
        r = await c.post("/auth/login", json={
            "email": "admin@recruitgen.ai", "password": "Admin@123456"
        })
        if r.status_code == 200:
            admin_token = r.json()["access_token"]
            log("Admin login", True)
        else:
            log("Admin login", False, f"HTTP {r.status_code}")
            admin_token = None

        admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

        # ── 3. Admin creates Recruiter ──
        print("\n-- ADMIN USER CREATION --")
        r = await c.post("/auth/admin/create-user", json={
            "email": "test_recruiter@e2e.com", "password": "Test@12345",
            "full_name": "E2E Recruiter", "role": "recruiter",
            "organization_name": "RecruitGen"
        }, headers=admin_headers)
        if r.status_code == 201:
            recruiter_token = r.json()["access_token"]
            log("Admin creates recruiter", True)
        elif r.status_code == 409 or "already" in r.text.lower():
            # Already exists, login instead
            r2 = await c.post("/auth/login", json={
                "email": "test_recruiter@e2e.com", "password": "Test@12345"
            })
            recruiter_token = r2.json().get("access_token") if r2.status_code == 200 else None
            log("Admin creates recruiter", recruiter_token is not None, "Already existed, logged in")
        else:
            recruiter_token = None
            log("Admin creates recruiter", False, f"HTTP {r.status_code}: {r.text[:100]}")

        # ── 4. Admin creates HR ──
        r = await c.post("/auth/admin/create-user", json={
            "email": "test_hr@e2e.com", "password": "Test@12345",
            "full_name": "E2E HR Manager", "role": "hr_manager",
            "organization_name": "RecruitGen"
        }, headers=admin_headers)
        if r.status_code == 201:
            hr_token = r.json()["access_token"]
            log("Admin creates HR", True)
        elif r.status_code == 409 or "already" in r.text.lower():
            r2 = await c.post("/auth/login", json={
                "email": "test_hr@e2e.com", "password": "Test@12345"
            })
            hr_token = r2.json().get("access_token") if r2.status_code == 200 else None
            log("Admin creates HR", hr_token is not None, "Already existed, logged in")
        else:
            hr_token = None
            log("Admin creates HR", False, f"HTTP {r.status_code}: {r.text[:100]}")

        # ── 5. Candidate registration ──
        r = await c.post("/auth/register", json={
            "email": "test_candidate@e2e.com", "password": "Test@12345",
            "full_name": "E2E Candidate", "role": "candidate",
            "organization_name": "RecruitGen"
        })
        if r.status_code == 201:
            cand_token = r.json()["access_token"]
            log("Candidate registration", True)
        elif r.status_code == 409 or "already" in r.text.lower():
            r2 = await c.post("/auth/login", json={
                "email": "test_candidate@e2e.com", "password": "Test@12345"
            })
            cand_token = r2.json().get("access_token") if r2.status_code == 200 else None
            log("Candidate registration", cand_token is not None, "Already existed, logged in")
        else:
            cand_token = None
            log("Candidate registration", False, f"HTTP {r.status_code}: {r.text[:100]}")

        recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"} if recruiter_token else {}
        hr_headers = {"Authorization": f"Bearer {hr_token}"} if hr_token else {}
        cand_headers = {"Authorization": f"Bearer {cand_token}"} if cand_token else {}

        # ── 6. User listing (admin) ──
        print("\n-- USER MANAGEMENT --")
        r = await c.get("/users/", headers=admin_headers)
        users = r.json() if r.status_code == 200 else []
        log("List users (admin)", r.status_code == 200, f"{len(users)} users")

        # ── 7. User toggle test ──
        non_admin = next((u for u in users if u.get("role") != "admin"), None)
        if non_admin:
            r = await c.patch(f"/users/{non_admin['id']}/toggle-active", headers=admin_headers)
            log("Toggle user active", r.status_code == 200,
                f"{non_admin['full_name']}: is_active={r.json().get('is_active')}" if r.status_code == 200 else f"HTTP {r.status_code}")
            # Toggle back
            await c.patch(f"/users/{non_admin['id']}/toggle-active", headers=admin_headers)
        else:
            log("Toggle user active", False, "No non-admin user found")

        # -- 8. Recruiter creates job --
        print("\n-- RECRUITER WORKFLOW --")
        r = await c.post("/jobs/", json={
            "title": "E2E ML Engineer",
            "description": "Machine learning engineer for testing the full recruitment pipeline.",
            "requirements": "Python, TensorFlow, PyTorch, 3+ years ML experience",
            "location": "Hyderabad",
            "employment_type": "full_time",
            "experience_level": "mid",
            "status": "active",
        }, headers=recruiter_headers)
        if r.status_code == 201:
            job = r.json()
            job_id = job["id"]
            log("Create job", True, f"'{job['title']}' (status={job.get('status', 'N/A')})")
        else:
            job_id = None
            log("Create job", False, f"HTTP {r.status_code}: {r.text[:100]}")

        # -- 9. List jobs --
        r = await c.get("/jobs/", headers=recruiter_headers)
        jobs = r.json() if r.status_code == 200 else []
        log("List jobs", r.status_code == 200, f"{len(jobs)} jobs")
        if not job_id and jobs:
            job_id = jobs[0]["id"]

        # -- 10. Candidate applies --
        print("\n-- CANDIDATE WORKFLOW --")
        app_id = None
        if job_id and cand_token:
            r = await c.post("/applications/", json={
                "job_id": job_id,
            }, headers=cand_headers)
            if r.status_code == 201:
                app_data = r.json()
                app_id = app_data["id"]
                log("Apply to job", True, f"status={app_data.get('status', 'N/A')}")
            elif r.status_code == 409 or "already" in r.text.lower():
                log("Apply to job", True, "Already applied")
            else:
                log("Apply to job", False, f"HTTP {r.status_code}: {r.text[:100]}")

        # -- 11. List candidate applications --
        r = await c.get("/applications/me", headers=cand_headers)
        apps = r.json() if r.status_code == 200 else []
        log("List my applications", r.status_code == 200, f"{len(apps)} applications")
        if not app_id and apps:
            app_id = apps[0].get("id")

        # -- 12. Notifications --
        print("\n-- NOTIFICATION TESTS --")
        r = await c.get("/notifications/unread-count", headers=cand_headers)
        log("Unread count (candidate)", r.status_code == 200,
            f"count={r.json().get('count', r.json())}" if r.status_code == 200 else f"HTTP {r.status_code}")

        r = await c.get("/notifications/", headers=admin_headers)
        log("List notifications (admin)", r.status_code == 200,
            f"{len(r.json()) if r.status_code == 200 else 0} notifications")

        # -- 13. Reports --
        print("\n-- REPORT TESTS --")
        r = await c.post("/reports/", json={
            "report_type": "hiring",
            "title": "E2E Hiring Report",
        }, headers=admin_headers)
        if r.status_code == 200:
            report = r.json()
            report_id = report.get("id")
            log("Generate hiring report", True, f"status={report.get('status')}")

            # Test CSV export
            if report_id:
                r = await c.get(f"/reports/{report_id}/csv", headers=admin_headers)
                log("CSV export", r.status_code == 200, f"Content-Type={r.headers.get('content-type', 'N/A')}")

                r = await c.get(f"/reports/{report_id}/download", headers=admin_headers)
                log("PDF export", r.status_code == 200, f"size={len(r.content)} bytes" if r.status_code == 200 else f"HTTP {r.status_code}")

                r = await c.get(f"/reports/{report_id}/excel", headers=admin_headers)
                log("Excel export", r.status_code == 200, f"size={len(r.content)} bytes" if r.status_code == 200 else f"HTTP {r.status_code}")
        else:
            log("Generate hiring report", False, f"HTTP {r.status_code}: {r.text[:100]}")

        r = await c.post("/reports/", json={
            "report_type": "analytics",
            "title": "E2E Analytics Report",
        }, headers=admin_headers)
        log("Generate analytics report", r.status_code == 200,
            f"status={r.json().get('status')}" if r.status_code == 200 else f"HTTP {r.status_code}")

        # -- 14. Pipeline stage enforcement --
        print("\n-- PIPELINE ENFORCEMENT --")
        if app_id:
            # Invalid: applied -> selected (skip stages)
            r = await c.patch(f"/applications/{app_id}/status", json={
                "status": "selected"
            }, headers=recruiter_headers)
            log("Block invalid transition (applied->selected)",
                r.status_code == 422,
                f"HTTP {r.status_code}" + (f": {r.json().get('detail', '')[:80]}" if r.status_code != 200 else ""))

            # Valid: applied -> screened
            r = await c.patch(f"/applications/{app_id}/status", json={
                "status": "screened"
            }, headers=recruiter_headers)
            log("Valid transition (applied->screened)",
                r.status_code == 200,
                f"HTTP {r.status_code}")

            # Valid: screened -> shortlisted
            r = await c.patch(f"/applications/{app_id}/status", json={
                "status": "shortlisted"
            }, headers=recruiter_headers)
            log("Valid transition (screened->shortlisted)",
                r.status_code == 200,
                f"HTTP {r.status_code}")

            # Invalid: shortlisted -> selected (skip interview)
            r = await c.patch(f"/applications/{app_id}/status", json={
                "status": "selected"
            }, headers=recruiter_headers)
            log("Block skip (shortlisted->selected)",
                r.status_code == 422,
                f"HTTP {r.status_code}" + (f": {r.json().get('detail', '')[:80]}" if r.status_code != 200 else ""))

        # ── SUMMARY ──
        print("\n" + "="*60)
        passed = sum(1 for _, p, _ in RESULTS if p)
        total = len(RESULTS)
        failed = total - passed
        print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
        print("="*60)

        if failed > 0:
            print("\n  FAILURES:")
            for test, p, detail in RESULTS:
                if not p:
                    print(f"    FAIL: {test}: {detail}")

        print()

if __name__ == "__main__":
    asyncio.run(main())
