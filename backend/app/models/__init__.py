"""
SQLAlchemy ORM Models.

All models are imported here so Alembic can discover them
for auto-generated migrations.
"""

from app.models.organization import Organization  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.job import Job, JobRequirement, JobStatus  # noqa: F401
from app.models.application import Application, ApplicationStatus  # noqa: F401
from app.models.resume import Resume  # noqa: F401

# ── AI Core Models ──────────────────────────────────────────
from app.models.candidate import (  # noqa: F401
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateProfile,
    CandidateProject,
    CandidateSkill,
    ParserSource,
    ParsingStatus,
)
from app.models.job_analysis import AnalysisStatus, JobAnalysis  # noqa: F401
from app.models.candidate_match import CandidateMatch  # noqa: F401
from app.models.candidate_ranking import CandidateRanking  # noqa: F401

# ── Agent Models ────────────────────────────────────────────
from app.models.interview_schedule import (  # noqa: F401
    InterviewSchedule,
    InterviewStatus,
    InterviewType,
)
from app.models.notification import Notification, NotificationType  # noqa: F401
from app.models.report import Report, ReportStatus, ReportType  # noqa: F401
from app.models.skill_evaluation import EvaluationType, SkillEvaluation  # noqa: F401
from app.models.hiring_recommendation import (  # noqa: F401
    HiringDecision,
    HiringRecommendation,
)
