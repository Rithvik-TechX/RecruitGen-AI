# API Documentation — RecruitmentGen AI

Base URL: `http://localhost:8000/api/v1`

## Authentication

All endpoints except `/auth/register` and `/auth/login` require a JWT Bearer token.

### Register
```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "candidate"  // admin | recruiter | candidate | hr_manager
}

Response: 201 Created
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "candidate",
  "is_active": true
}
```

### Login
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword

Response: 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token
```
POST /auth/refresh
Authorization: Bearer <refresh_token>

Response: 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Users

### Get Current User
```
GET /users/me
Authorization: Bearer <token>

Response: 200 OK
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "candidate",
  "organization_id": "uuid",
  "is_active": true
}
```

---

## Jobs

### List Jobs
```
GET /jobs?status=active
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": "uuid",
    "title": "Senior Software Engineer",
    "description": "...",
    "department": "Engineering",
    "location": "Remote",
    "salary_min": 80000,
    "salary_max": 120000,
    "job_type": "full_time",
    "status": "active",
    "created_at": "2026-06-01T00:00:00"
  }
]
```

### Create Job
```
POST /jobs
Authorization: Bearer <token> (recruiter/admin only)
Content-Type: application/json

{
  "title": "Senior Software Engineer",
  "description": "We are looking for...",
  "department": "Engineering",
  "location": "Remote",
  "salary_min": 80000,
  "salary_max": 120000,
  "job_type": "full_time"
}
```

---

## Applications

### Apply to Job
```
POST /applications
Authorization: Bearer <token> (candidate only)
Content-Type: application/json

{
  "job_id": "uuid"
}
```

### Get My Applications
```
GET /applications/me
Authorization: Bearer <token>
```

### Update Application Status
```
PATCH /applications/{id}/status
Authorization: Bearer <token> (recruiter/admin only)
Content-Type: application/json

{
  "status": "screened"  // applied | screened | shortlisted | rejected | accepted
}
```

---

## Resumes

### Upload Resume
```
POST /resumes/upload
Authorization: Bearer <token> (candidate only)
Content-Type: multipart/form-data

file: <PDF or DOCX file, max 10MB>
```

### List My Resumes
```
GET /resumes/me
Authorization: Bearer <token>
```

---

## AI — Resume Intelligence

### Parse Resume with AI
```
POST /resumes/parse/{resume_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "candidate_id": "uuid",
  "parsing_status": "completed",
  "profile": { ... }
}
```

---

## AI — Job Intelligence

### Analyze Job Description
```
POST /jobs/{job_id}/analyze
Authorization: Bearer <token>

Response: 200 OK
{
  "required_skills": [...],
  "preferred_skills": [...],
  "education_requirements": {...},
  "experience_requirements": {...},
  "analysis_summary": "..."
}
```

### Match Candidates to Job
```
POST /jobs/{job_id}/match
Authorization: Bearer <token>

Response: 200 OK
{
  "matches": [
    {
      "candidate_id": "uuid",
      "overall_match_score": 85.5,
      "skill_match_score": 90.0,
      "experience_match_score": 80.0,
      "education_match_score": 75.0,
      "semantic_similarity_score": 88.0
    }
  ]
}
```

### Rank Candidates
```
POST /jobs/{job_id}/rank
Authorization: Bearer <token>

Response: 200 OK
{
  "rankings": [
    {
      "candidate_id": "uuid",
      "rank_position": 1,
      "final_score": 87.5,
      "skill_score": 90.0,
      "experience_score": 85.0
    }
  ]
}
```

---

## AI — Skill Evaluation

### Evaluate Candidate
```
POST /jobs/{job_id}/evaluate/{candidate_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "technical_score": 85.0,
  "competency_scores": {
    "programming": 90,
    "frameworks": 80,
    "databases": 75
  },
  "skill_gaps": [
    {"skill": "Kubernetes", "importance": "important", "suggestion": "..."}
  ],
  "strengths": ["Strong Python skills", "..."],
  "evaluation_summary": "..."
}
```

---

## AI — Hiring Recommendation

### Generate Recommendation
```
POST /jobs/{job_id}/recommend/{candidate_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "decision": "hire",
  "confidence_score": 0.85,
  "risk_assessment": "Low risk hire...",
  "strengths": [{"area": "Technical", "detail": "..."}],
  "weaknesses": [{"area": "Experience", "detail": "..."}],
  "reasoning": "...",
  "summary": "Recommended for hire"
}
```

---

## AI — Full Pipeline

### Run Complete Pipeline
```
POST /pipeline/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "resume_id": "uuid",
  "job_id": "uuid"
}

Response: 200 OK
{
  "completed": true,
  "candidate_id": "uuid",
  "match_results": [...],
  "ranking_results": [...],
  "evaluation_results": [...],
  "recommendation_results": [...]
}
```

---

## Analytics

### Dashboard Stats
```
GET /analytics/dashboard
Authorization: Bearer <token>

Response: 200 OK
{
  "stats": {
    "total_jobs": 15,
    "total_candidates": 120,
    "total_applications": 350,
    "hiring_rate": 12.5
  },
  "pipeline": {
    "active_jobs": 8,
    "pending_reviews": 25,
    "interviews_this_week": 12
  },
  "top_skills": [
    {"skill_name": "Python", "count": 45, "percentage": 18.5}
  ]
}
```

### Skills Distribution
```
GET /analytics/skills

Response: 200 OK
[
  {"skill_name": "Python", "count": 45, "percentage": 18.5},
  {"skill_name": "JavaScript", "count": 38, "percentage": 15.6}
]
```

---

## Interviews

### Schedule Interview
```
POST /jobs/{job_id}/interviews
Authorization: Bearer <token>
Content-Type: application/json

{
  "candidate_id": "uuid",
  "scheduled_at": "2026-06-15T10:00:00",
  "duration_minutes": 60,
  "interview_type": "video",
  "meeting_link": "https://meet.google.com/xxx",
  "notes": "Technical interview"
}
```

---

## Reports

### Generate Candidate Report
```
POST /reports/candidate/{candidate_id}
Authorization: Bearer <token>
```

### Generate Hiring Report
```
POST /reports/hiring/{job_id}
Authorization: Bearer <token>
```

### List Reports
```
GET /reports
Authorization: Bearer <token>
```

### Download Report PDF
```
GET /reports/{report_id}/download
Authorization: Bearer <token>

Response: PDF file
```

---

## Notifications

### List Notifications
```
GET /notifications
Authorization: Bearer <token>
```

### Get Unread Count
```
GET /notifications/unread-count

Response: {"unread_count": 5}
```

### Mark as Read
```
PATCH /notifications/{id}/read
Authorization: Bearer <token>
```
