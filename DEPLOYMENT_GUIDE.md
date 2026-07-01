# Deployment Guide — RecruitmentGen AI

## Prerequisites

- Docker Desktop (v24+) with Docker Compose v2
- Node.js 18+ and npm 9+
- Git
- A Google Gemini API Key ([Generate here](https://aistudio.google.com/app/apikey))

---

## Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd RecruitmentGEN-AI
```

## Step 2: Configure Environment Variables

Edit the `.env` file in the project root:

```env
# REQUIRED — Set your Gemini API Key
GEMINI_API_KEY=your-actual-gemini-api-key

# These defaults work for local development:
POSTGRES_USER=recruitgen
POSTGRES_PASSWORD=recruitgen_secret
POSTGRES_DB=recruitgen_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

JWT_SECRET_KEY=dev-only-jwt-secret-change-in-production
SECRET_KEY=change-me-in-production

BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

## Step 3: Start Backend Services

```bash
# Start PostgreSQL, ChromaDB, and FastAPI backend
docker compose up --build -d

# Verify services are running
docker compose ps

# Check backend logs
docker compose logs backend -f
```

Expected output:
- PostgreSQL on port `5432`
- ChromaDB on port `8001`
- FastAPI Backend on port `8000`

## Step 4: Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

This creates all 14+ database tables.

## Step 5: Verify Backend

```bash
# Health check
curl http://localhost:8000/health

# Database check
curl http://localhost:8000/health/db

# Swagger docs
open http://localhost:8000/docs
```

## Step 6: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

## Step 7: Create Test Users

Open `http://localhost:3000/register` and create accounts:

1. **Admin**: admin@test.com / password123
2. **Recruiter**: recruiter@test.com / password123
3. **Candidate**: candidate@test.com / password123
4. **HR Manager**: hr@test.com / password123

---

## Demo Walkthrough

### Phase 1: Job Setup (Recruiter)
1. Login as Recruiter
2. Go to Jobs → Create New Job
3. Fill in job details (title, description, requirements)
4. Click "Analyze" to run AI analysis

### Phase 2: Candidate Application
1. Login as Candidate
2. Go to Profile → Upload Resume (PDF/DOCX)
3. Click "Parse with AI" to extract profile data
4. Go to Jobs → Apply to a position

### Phase 3: AI Processing (Recruiter)
1. Login as Recruiter
2. Go to Rankings → Select Job → "Run AI Ranking"
3. View ranked candidates with scores

### Phase 4: HR Decision (HR Manager)
1. Login as HR Manager
2. Go to Candidates → Select Job
3. Click "Evaluate" on a candidate → AI generates skill assessment
4. Click "Recommend" → AI generates hiring recommendation

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check `.env` file, ensure Docker is running |
| Database connection error | Run `docker compose restart db` |
| AI features return errors | Verify `GEMINI_API_KEY` in `.env` |
| Frontend 401 errors | Clear localStorage and re-login |
| ChromaDB connection error | Run `docker compose restart chromadb` |

## Stopping Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (resets database)
docker compose down -v
```
