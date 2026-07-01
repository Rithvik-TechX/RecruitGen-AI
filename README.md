# RecruitmentGen AI

> Multi-Agent Intelligent Recruitment System powered by AI

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Gemini](https://img.shields.io/badge/Gemini_AI-886FBF?style=flat&logo=google&logoColor=white)](https://ai.google.dev)

---

## Overview

RecruitmentGen AI is a comprehensive AI-powered recruitment platform that automates and enhances the hiring process using multiple specialized AI agents. The system handles everything from resume parsing to hiring recommendations, providing a complete end-to-end recruitment workflow.

### Key Features

| Feature | Description |
|---------|-------------|
| **AI Resume Parsing** | Extracts structured data from PDF/DOCX resumes using Gemini 2.5 Flash |
| **Job Description Analysis** | AI-powered analysis of job requirements, skills, and qualifications |
| **Semantic Matching** | Vector-based candidate-job matching using sentence transformers & ChromaDB |
| **AI Ranking** | Multi-dimensional candidate ranking with weighted scoring |
| **Skill Evaluation** | AI-generated technical competency assessments |
| **Hiring Recommendations** | AI-powered hire/consider/reject decisions with confidence scores |
| **LangGraph Pipeline** | Orchestrated multi-agent workflow for end-to-end processing |
| **Role-Based Access** | Admin, Recruiter, HR Manager, and Candidate dashboards |

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| AI Model | Google Gemini 2.5 Flash |
| Embeddings | Sentence Transformers (BAAI/bge-small-en-v1.5) |
| Vector Store | ChromaDB |
| Orchestration | LangGraph |
| Auth | JWT (python-jose + bcrypt) |
| PDF Reports | ReportLab |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS v4 |
| State | TanStack React Query v5 |
| HTTP | Axios |
| Charts | Recharts |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containers | Docker + Docker Compose |
| Database | PostgreSQL 16 Alpine |
| Vector DB | ChromaDB (persistent) |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- A Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### 1. Clone & Configure

```bash
git clone <repo-url>
cd RecruitmentGEN-AI

# Set your Gemini API key
# Edit .env and replace GEMINI_API_KEY=your-gemini-api-key-here
```

### 2. Start Backend (Docker)

```bash
docker compose up --build
```

### 3. Run Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## Demo Flow

### 1. Register Users
- Create a **Recruiter** account
- Create a **Candidate** account
- Create an **HR Manager** account

### 2. Recruiter Workflow
1. Login as Recruiter → Create a job posting
2. Analyze the job with AI → View extracted requirements
3. View applications → Run AI matching
4. Run AI ranking → View ranked candidates
5. Schedule interviews → Generate reports

### 3. Candidate Workflow
1. Login as Candidate → Upload resume (PDF/DOCX)
2. AI parses resume → Creates structured profile
3. Browse jobs → Apply to positions
4. Track application status

### 4. HR Manager Workflow
1. Login as HR → View candidate pipeline
2. Run AI skill evaluations
3. Generate hiring recommendations (hire/consider/reject)
4. Review and schedule interviews

---

## Project Structure

```
RecruitmentGEN-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── core/                   # Config, security, logging
│   │   ├── db/                     # Database engine, session, base
│   │   ├── models/                 # SQLAlchemy ORM models (14 models)
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── api/v1/endpoints/       # API route handlers (15 routers)
│   │   ├── services/               # Business logic (16 services)
│   │   ├── repositories/           # Data access layer (17 repos)
│   │   ├── providers/              # AI providers (Gemini, embeddings)
│   │   ├── vector_store/           # ChromaDB integration
│   │   ├── domain/langgraph/       # LangGraph pipeline
│   │   └── utils/                  # Resume text extraction
│   ├── alembic/                    # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js pages (20+ pages)
│   │   ├── components/             # Reusable UI components
│   │   ├── context/                # Auth context
│   │   ├── lib/                    # API client, hooks, utilities
│   │   └── types/                  # TypeScript interfaces
│   └── package.json
├── docker-compose.yml
└── .env
```

---

## API Documentation

The complete API documentation is available at `/docs` (Swagger UI) when the backend is running.

### Key Endpoints

| Category | Endpoints |
|----------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` |
| Jobs | `GET/POST /jobs`, `PATCH /jobs/{id}` |
| Applications | `POST /applications`, `GET /applications/me` |
| Resumes | `POST /resumes/upload`, `GET /resumes/me` |
| AI Resume | `POST /resumes/parse/{id}` |
| AI Jobs | `POST /jobs/{id}/analyze`, `POST /jobs/{id}/match`, `POST /jobs/{id}/rank` |
| Evaluations | `POST /jobs/{id}/evaluate/{cid}` |
| Recommendations | `POST /jobs/{id}/recommend/{cid}` |
| Pipeline | `POST /pipeline/run` |
| Interviews | `POST /jobs/{id}/interviews` |
| Analytics | `GET /analytics/dashboard`, `GET /analytics/skills` |
| Reports | `POST /reports/candidate/{id}`, `POST /reports/hiring/{id}` |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend (Next.js)                 │
│     Dashboard • Forms • Charts • Auth           │
├─────────────────────────────────────────────────┤
│              REST API (FastAPI)                  │
│    Auth • Jobs • Applications • AI Pipeline     │
├─────────────────────────────────────────────────┤
│           Business Logic (Services)             │
│  Matching • Ranking • Evaluation • Reports      │
├─────────────────────────────────────────────────┤
│          AI Layer (Providers)                    │
│  Gemini 2.5 Flash • Sentence Transformers       │
├─────────────────────────────────────────────────┤
│          Data Layer                              │
│  PostgreSQL • ChromaDB • Alembic                │
├─────────────────────────────────────────────────┤
│       Orchestration (LangGraph)                  │
│  Parse → Profile → Analyze → Match → Rank →     │
│  Evaluate → Recommend                           │
└─────────────────────────────────────────────────┘
```

---

## License

Proprietary — All rights reserved.

## Authors

RecruitmentGen AI Team — Final Year AIML Project, 2026
