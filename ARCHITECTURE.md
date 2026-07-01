# Architecture — RecruitmentGen AI

## System Overview

RecruitmentGen AI follows a **Clean Architecture** pattern with clear separation of concerns across multiple layers.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│  Next.js 16 │ React 19 │ TypeScript │ Tailwind CSS v4       │
│  React Query │ Axios │ Recharts                              │
├──────────────────────────────────────────────────────────────┤
│                    API GATEWAY                               │
│  FastAPI │ CORS │ JWT Auth │ Rate Limiting                   │
│  15 Routers │ ~40 Endpoints │ Swagger/ReDoc                  │
├──────────────────────────────────────────────────────────────┤
│                APPLICATION LAYER                             │
│  16 Service Classes │ Business Logic │ Validation            │
│  Auth │ Jobs │ Applications │ Resumes │ Analytics │ Reports  │
├──────────────────────────────────────────────────────────────┤
│               AI / INTELLIGENCE LAYER                        │
│  ┌─────────────┐ ┌────────────┐ ┌──────────────────┐        │
│  │ Gemini 2.5  │ │ Sentence   │ │    LangGraph     │        │
│  │ Flash       │ │ Transformers│ │   Orchestrator   │        │
│  │             │ │ (BGE-small)│ │                  │        │
│  │ • Parse     │ │            │ │ Parse → Profile  │        │
│  │ • Analyze   │ │ • Embed    │ │ → Analyze → Match│        │
│  │ • Evaluate  │ │ • Cosine   │ │ → Rank → Eval   │        │
│  │ • Recommend │ │   Sim      │ │ → Recommend      │        │
│  └─────────────┘ └────────────┘ └──────────────────┘        │
├──────────────────────────────────────────────────────────────┤
│                DATA ACCESS LAYER                             │
│  17 Repository Classes │ Generic CRUD Base                   │
│  SQLAlchemy 2.0 Async │ Eager Loading │ Relationships        │
├──────────────────────────────────────────────────────────────┤
│                  DATA STORES                                 │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ PostgreSQL   │  │  ChromaDB    │                         │
│  │ 16 Alpine    │  │  Vector DB   │                         │
│  │              │  │              │                         │
│  │ 14 Tables    │  │ 2 Collections│                         │
│  │ 6 Migrations │  │ • candidates │                         │
│  │ UUID PKs     │  │ • jobs       │                         │
│  └──────────────┘  └──────────────┘                         │
└──────────────────────────────────────────────────────────────┘
```

## AI Pipeline Flow

```
Resume Upload (PDF/DOCX)
        │
        ▼
┌─────────────────────┐
│ Text Extraction     │  PyMuPDF / python-docx
│ (resume_parser.py)  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ AI Resume Parsing   │  Gemini 2.5 Flash
│ (gemini_provider)   │  → Structured JSON
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Candidate Profile   │  Skills, Education, Experience,
│ Creation            │  Projects, Certifications
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Embedding           │  sentence-transformers
│ Generation          │  BAAI/bge-small-en-v1.5
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ ChromaDB Storage    │  Candidate + Job embeddings
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Multi-Dim Matching  │  Skill (40%) + Experience (25%)
│ (matching_service)  │  + Education (15%) + Semantic (20%)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Weighted Ranking    │  Skill (40%) + Exp (25%) + Edu (15%)
│ (ranking_service)   │  + Project (10%) + Semantic (10%)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Skill Evaluation    │  Gemini AI → Technical scores,
│                     │  Competency breakdown, Gaps
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Hiring              │  Gemini AI → Hire/Consider/Reject
│ Recommendation      │  Confidence, Risk, Strengths
└─────────────────────┘
```

## Database Schema

### Core Tables
- `organizations` — Company/org info
- `users` — All user accounts with roles (admin, recruiter, candidate, hr_manager)
- `jobs` — Job postings with status lifecycle
- `job_requirements` — Structured job requirements
- `applications` — Candidate-job applications
- `resumes` — Uploaded resume files + extracted text

### AI Pipeline Tables
- `candidate_profiles` — AI-parsed candidate profiles
- `candidate_skills` — Extracted skills with proficiency
- `candidate_education` — Education history
- `candidate_experiences` — Work experience
- `candidate_projects` — Projects
- `candidate_certifications` — Certifications
- `job_analyses` — AI-analyzed job requirements
- `candidate_matches` — Match scores per candidate-job pair
- `candidate_rankings` — Ranked positions with scores
- `skill_evaluations` — AI competency assessments
- `hiring_recommendations` — AI hire/consider/reject decisions

### Operational Tables
- `interview_schedules` — Interview scheduling
- `notifications` — User notifications
- `reports` — Generated reports (JSON + PDF)

## Authentication & Authorization

- **JWT-based** authentication with access + refresh tokens
- **RBAC** (Role-Based Access Control) via dependency injection
- Roles: `admin`, `recruiter`, `candidate`, `hr_manager`
- Route-level authorization checks in API endpoints

## Frontend Architecture

```
src/
├── app/              # Next.js App Router pages
│   ├── login/        # Auth pages
│   ├── register/
│   ├── admin/        # Admin dashboard (4 pages)
│   ├── recruiter/    # Recruiter dashboard (7 pages)
│   ├── candidate/    # Candidate dashboard (5 pages)
│   └── hr/           # HR Manager dashboard (5 pages)
├── components/
│   ├── layout/       # Shell, Sidebar, Navbar
│   └── ui/           # Reusable UI components
├── context/          # Auth context (JWT + user state)
├── lib/              # API client, hooks (30+ hooks), utilities
└── types/            # TypeScript interfaces (345 lines)
```
