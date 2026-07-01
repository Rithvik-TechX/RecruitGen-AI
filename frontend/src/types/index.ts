/**
 * TypeScript interfaces matching the FastAPI backend schemas.
 */

// ── Enums ──────────────────────────────────────────────────

export type UserRole = "admin" | "recruiter" | "candidate" | "hr_manager";
export type JobType = "full_time" | "part_time" | "contract" | "internship";
export type JobStatus = "draft" | "active" | "paused" | "closed" | "archived";
export type ApplicationStatus = "applied" | "screened" | "shortlisted" | "interview_scheduled" | "interview_completed" | "selected" | "rejected";
export type ParsingStatus = "pending" | "processing" | "completed" | "failed";
export type ParserSource = "ai" | "fallback";
export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";
export type InterviewType = "phone" | "video" | "onsite" | "technical" | "hr" | "panel";
export type InterviewStatus = "scheduled" | "confirmed" | "in_progress" | "completed" | "cancelled" | "no_show" | "rescheduled";
export type NotificationType = "interview_invite" | "shortlisted" | "rejection" | "offer" | "application_update" | "general";
export type ReportType = "candidate" | "hiring" | "match" | "interview" | "analytics";

export interface AIStatus {
  state: "ACTIVE" | "FALLBACK" | "UNAVAILABLE";
  provider: string;
  model: string;
  message: string;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  last_error?: string | null;
}
export type ReportStatus = "pending" | "generating" | "completed" | "failed";
export type EvaluationType = "ai" | "manual" | "hybrid";
export type HiringDecision = "hire" | "consider" | "reject";

// ── Auth ───────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  organization_name: string;
  industry?: string;
  company_size?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  organization?: Organization;
  created_at: string;
  updated_at: string;
}

// ── Organizations ──────────────────────────────────────────

export interface Organization {
  id: string;
  name: string;
  industry?: string;
  company_size?: string;
  member_count?: number;
  created_at: string;
  updated_at?: string;
}

// ── Jobs ───────────────────────────────────────────────────

export interface Job {
  id: string;
  title: string;
  description?: string;
  department?: string;
  experience_required?: string;
  requirements?: string;
  responsibilities?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  employment_type?: string;
  status: JobStatus;
  organization_id: string;
  recruiter_id: string;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  title: string;
  description?: string;
  department?: string;
  location?: string;
  employment_type?: string;
  experience_required?: string;
  salary_min?: number;
  salary_max?: number;
  status?: JobStatus;
}

// ── Applications ───────────────────────────────────────────

export interface Application {
  id: string;
  job_id: string;
  candidate_id: string;
  status: ApplicationStatus;
  applied_at: string;
  updated_at: string;
  candidate_name?: string;
  job_title?: string;
  candidate_profile_id?: string;
  overall_match_score?: number;
  skill_match_score?: number;
  experience_match_score?: number;
  rank_position?: number;
  final_score?: number;
}

// ── Candidate ──────────────────────────────────────────────

export interface CandidateSkill {
  id: string;
  skill_name: string;
  proficiency_level?: string;
  years_of_experience?: number;
  category?: string;
}

export interface CandidateEducation {
  id: string;
  institution: string;
  degree?: string;
  field_of_study?: string;
  start_date?: string;
  end_date?: string;
  gpa?: string;
}

export interface CandidateExperience {
  id: string;
  company: string;
  title: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
  technologies?: string;
}

export interface CandidateProfile {
  id: string;
  resume_id: string;
  full_name: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  summary?: string;
  parsing_status: ParsingStatus;
  parser_source: ParserSource;
  skills: CandidateSkill[];
  education: CandidateEducation[];
  experiences: CandidateExperience[];
  projects: CandidateProject[];
  certifications: CandidateCertification[];
  achievements: CandidateAchievement[];
  internships: CandidateInternship[];
  awards: CandidateAward[];
  publications: CandidatePublication[];
  research_experience: CandidateResearchExperience[];
  languages: string[];
  links: CandidateLink[];
  created_at: string;
}

export interface ResumeResponse {
  id: string;
  candidate_id: string;
  file_name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  raw_text?: string;
  parsed_data?: Record<string, unknown>;
  uploaded_at: string;
}

export interface ResumeUploadResponse {
  id: string;
  candidate_id: string;
  file_name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  raw_text?: string;
  parsed_data?: Record<string, unknown>;
  uploaded_at: string;
}

export interface CandidateProject {
  id: string;
  project_name: string;
  description?: string;
  technologies?: string;
  year?: string;
  url?: string;
}

export interface CandidateCertification {
  id: string;
  certification_name: string;
  issuing_organization?: string;
  issue_date?: string;
  credential_url?: string;
}

export interface CandidateAchievement {
  title: string;
  description?: string;
  date?: string;
}

export interface CandidateInternship {
  company: string;
  role: string;
  duration?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
  technologies: string[];
}

export interface CandidateAward {
  title: string;
  issuer?: string;
  date?: string;
  description?: string;
}

export interface CandidatePublication {
  title: string;
  publisher?: string;
  publication_date?: string;
  url?: string;
  description?: string;
}

export interface CandidateLink {
  link_type: string;
  label?: string;
  url: string;
}

export interface CandidateResearchExperience {
  title: string;
  description?: string;
  duration?: string;
}

// ── Matching & Ranking ─────────────────────────────────────

export interface CandidateMatch {
  id: string;
  candidate_id: string;
  job_id: string;
  candidate_name?: string;
  skill_match_score: number;
  experience_match_score: number;
  education_match_score: number;
  semantic_similarity_score: number;
  overall_match_score: number;
  match_details?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface CandidateRanking {
  id: string;
  candidate_id: string;
  job_id: string;
  candidate_name?: string;
  rank_position: number;
  skill_score: number;
  experience_score: number;
  education_score: number;
  project_score: number;
  semantic_score: number;
  final_score: number;
  ranking_details?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

// ── Interviews ─────────────────────────────────────────────

export interface InterviewSchedule {
  id: string;
  candidate_id: string;
  job_id: string;
  interviewer_id?: string;
  scheduled_at: string;
  duration_minutes: number;
  interview_type: InterviewType;
  status: InterviewStatus;
  meeting_link?: string;
  location?: string;
  notes?: string;
  feedback?: string;
  created_at: string;
  updated_at?: string;
}

// ── Notifications ──────────────────────────────────────────

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

// ── Skill Evaluation ───────────────────────────────────────

export interface SkillEvaluation {
  id: string;
  candidate_id: string;
  job_id: string;
  technical_score: number;
  competency_scores?: Record<string, number>;
  skill_gaps?: Array<{ skill: string; importance: string; suggestion: string }>;
  strengths?: string[];
  evaluation_summary?: string;
  evaluated_by: EvaluationType;
}

// ── Hiring Recommendation ──────────────────────────────────

export interface HiringRecommendation {
  id: string;
  candidate_id: string;
  job_id: string;
  decision: HiringDecision;
  confidence_score: number;
  risk_assessment?: string;
  strengths?: Array<{ area: string; detail: string }>;
  weaknesses?: Array<{ area: string; detail: string }>;
  reasoning?: string;
  summary?: string;
  candidate_name?: string;
}

// ── Reports ────────────────────────────────────────────────

export interface ReportListItem {
  id: string;
  report_type: ReportType;
  title: string;
  summary?: string;
  organization_name: string;
  report_period: string;
  status: ReportStatus;
  created_at: string;
}

export interface ReportHeader {
  organization_name: string;
  generated_date: string;
  report_period: string;
}

export interface ReportCandidateInsight {
  candidate_name: string;
  job_applied: string;
  match_score?: number;
  skill_score?: number;
  recommendation?: HiringDecision;
  status: ApplicationStatus;
}

export interface ReportChartPoint {
  label: string;
  value: number;
}

export interface HiringReportData {
  kind: "hiring";
  header: ReportHeader;
  summary: {
    total_jobs: number;
    total_applications: number;
    screened: number;
    shortlisted: number;
    interviewed: number;
    selected: number;
    rejected: number;
  };
  pipeline: Array<{ stage: string; count: number }>;
  candidates: ReportCandidateInsight[];
  recommendation_summary: Record<HiringDecision, number>;
  top_skills: Array<{ skill_name: string; count: number }>;
  executive_summary: string;
}

export interface AnalyticsReportData {
  kind: "analytics";
  header: ReportHeader;
  summary: {
    applications: number;
    conversion_rate: number;
    average_match_score: number;
    average_skill_score: number;
  };
  application_trend: ReportChartPoint[];
  status_distribution: ReportChartPoint[];
  recommendation_distribution: ReportChartPoint[];
  match_score_distribution: ReportChartPoint[];
  executive_summary: string;
}

export interface MatchReportData {
  kind: "match";
  header: ReportHeader;
  summary: {
    total_matches: number;
    average_overall_score: number;
  };
  matches: Array<{
    candidate: string;
    overall_score: number;
    skill_score: number;
    experience_score: number;
    education_score: number;
    semantic_score: number;
  }>;
  executive_summary: string;
}

export interface GenericReportData {
  kind: "generic";
  header: ReportHeader;
  executive_summary: string;
}

export interface Report {
  id: string;
  report_type: ReportType;
  title: string;
  summary?: string;
  data: HiringReportData | AnalyticsReportData | MatchReportData | GenericReportData;
  status: ReportStatus;
  created_at: string;
  updated_at: string;
}

// ── Analytics ──────────────────────────────────────────────

export interface DashboardStats {
  total_jobs: number;
  total_candidates: number;
  total_applications: number;
  shortlisted: number;
  rejected: number;
  interviews_scheduled: number;
  hiring_rate: number;
}

export interface FunnelStage {
  stage: string;
  count: number;
  percentage: number;
}

export interface SkillDistribution {
  skill_name: string;
  count: number;
  percentage: number;
}

export interface PipelineMetrics {
  active_jobs: number;
  pending_reviews: number;
  interviews_this_week: number;
  avg_time_to_hire_days?: number;
}

export interface AnalyticsDashboard {
  stats: DashboardStats;
  pipeline: PipelineMetrics;
  top_skills: SkillDistribution[];
}

// ── Pipeline ───────────────────────────────────────────────

export interface PipelineResult {
  resume_id: string;
  job_id: string;
  candidate_id: string;
  candidate_profile: Record<string, unknown>;
  job_analysis: Record<string, unknown>;
  match_results: Array<Record<string, unknown>>;
  ranking_results: Array<Record<string, unknown>>;
  evaluation_results: Array<Record<string, unknown>>;
  recommendation_results: Array<Record<string, unknown>>;
  current_step: string;
  errors: string[];
  completed: boolean;
}
