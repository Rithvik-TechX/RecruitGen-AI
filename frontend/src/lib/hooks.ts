"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Application,
  InterviewSchedule,
  Job,
  JobCreate,
  JobStatus,
  ResumeResponse,
  ReportListItem,
  CandidateRanking,
  CandidateMatch,
  HiringRecommendation,
  SkillEvaluation,
  Notification,
  CandidateProfile,
  AIStatus,
} from "@/types";

/* ═══════════════════════════════════════════════════════════
   QUERY HOOKS — Read data
   ═══════════════════════════════════════════════════════════ */

export function useJobs(status?: JobStatus) {
  return useQuery<Job[]>({
    queryKey: ["jobs", status],
    queryFn: async () => {
      const params = status ? { status } : {};
      const res = await api.get<Job[]>("/jobs/", { params });
      return res.data;
    },
  });
}

export function useMyApplications() {
  return useQuery<Application[]>({
    queryKey: ["applications", "me"],
    queryFn: async () => {
      const res = await api.get<Application[]>("/applications/me");
      return res.data;
    },
  });
}

export function useApplicationsByJob(jobId: string | undefined) {
  return useQuery<Application[]>({
    queryKey: ["applications", "job", jobId],
    queryFn: async () => {
      const res = await api.get<Application[]>(`/jobs/${jobId}/applications`);
      return res.data;
    },
    enabled: Boolean(jobId),
  });
}

export function useHRCandidatePipeline(jobId?: string) {
  return useQuery<Application[]>({
    queryKey: ["applications", "pipeline", jobId || "all"],
    queryFn: async () => {
      const res = await api.get<Application[]>("/applications/pipeline", {
        params: jobId ? { job_id: jobId } : undefined,
      });
      return res.data;
    },
  });
}

export function useResumes() {
  return useQuery<ResumeResponse[]>({
    queryKey: ["resumes", "me"],
    queryFn: async () => {
      const res = await api.get<ResumeResponse[]>("/resumes/me");
      return res.data;
    },
  });
}

export function useCandidateProfile(candidateId: string | undefined) {
  return useQuery<CandidateProfile>({
    queryKey: ["candidate", candidateId],
    queryFn: async () => {
      const res = await api.get<CandidateProfile>(`/candidates/${candidateId}`);
      return res.data;
    },
    enabled: Boolean(candidateId),
  });
}

export function useAnalyticsDashboard() {
  return useQuery<{
    stats: Record<string, number>;
    pipeline: Record<string, number>;
    top_skills: Array<{ skill_name: string; count: number; percentage: number }>;
  }>({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => {
      const res = await api.get("/analytics/dashboard");
      return res.data;
    },
  });
}

export function useAnalyticsSkills() {
  return useQuery<Array<{ skill_name: string; count: number; percentage: number }>>({
    queryKey: ["analytics", "skills"],
    queryFn: async () => {
      const res = await api.get("/analytics/skills");
      return res.data;
    },
  });
}

export function useInterviews(jobId: string | undefined) {
  return useQuery<{ interviews: InterviewSchedule[]; total_count: number }>({
    queryKey: ["interviews", jobId],
    queryFn: async () => {
      const res = await api.get(`/jobs/${jobId}/interviews`);
      return res.data;
    },
    enabled: Boolean(jobId),
  });
}

export function useMyInterviews() {
  return useQuery<InterviewSchedule[]>({
    queryKey: ["interviews", "me"],
    queryFn: async () => {
      const res = await api.get<InterviewSchedule[]>("/interviews/me");
      return res.data;
    },
  });
}

export function useRankings(jobId: string | undefined) {
  return useQuery<{ rankings: CandidateRanking[]; total_count: number }>({
    queryKey: ["rankings", jobId],
    queryFn: async () => {
      const res = await api.get(`/jobs/${jobId}/rankings`);
      return res.data;
    },
    enabled: Boolean(jobId),
  });
}

export function useMatches(jobId: string | undefined) {
  return useQuery<{ matches: CandidateMatch[]; total_count: number }>({
    queryKey: ["matches", jobId],
    queryFn: async () => {
      const res = await api.get(`/jobs/${jobId}/matches`);
      return res.data;
    },
    enabled: Boolean(jobId),
  });
}

export function useRecommendations(jobId: string | undefined) {
  return useQuery<{ recommendations: HiringRecommendation[]; total_count: number }>({
    queryKey: ["recommendations", jobId],
    queryFn: async () => {
      const res = await api.get(`/jobs/${jobId}/recommendations`);
      return res.data;
    },
    enabled: Boolean(jobId),
  });
}

export function useEvaluations(jobId: string | undefined) {
  return useQuery<{ evaluations: SkillEvaluation[]; total_count: number }>({
    queryKey: ["evaluations", jobId],
    queryFn: async () => {
      const res = await api.get(`/jobs/${jobId}/evaluations`);
      return res.data;
    },
    enabled: Boolean(jobId),
  });
}

export function useNotifications() {
  return useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await api.get<{ notifications: Notification[]; unread_count: number; total_count: number }>("/notifications/");
      return res.data.notifications;
    },
  });
}

export function useUnreadCount() {
  return useQuery<{ count: number }>({
    queryKey: ["notifications", "unread"],
    queryFn: async () => {
      const res = await api.get<{ count: number }>("/notifications/unread-count");
      return res.data;
    },
    refetchInterval: 30000,
  });
}

export function useReports() {
  return useQuery<ReportListItem[]>({
    queryKey: ["reports"],
    queryFn: async () => {
      const res = await api.get<{ reports: ReportListItem[]; total_count: number }>("/reports/");
      return res.data.reports;
    },
  });
}

export function useSidebarCounts() {
  return useQuery<Record<string, number>>({
    queryKey: ["counts", "sidebar"],
    queryFn: async () => {
      const res = await api.get<Record<string, number>>("/counts/sidebar");
      return res.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000,
  });
}

export function useAIStatus() {
  return useQuery<AIStatus>({
    queryKey: ["ai", "status"],
    queryFn: async () => {
      const res = await api.get<AIStatus>("/ai/status");
      return res.data;
    },
    refetchInterval: 30000,
  });
}

/**
 * Mark a sidebar section as "seen" — resets the badge count for that section.
 * Call this when the user navigates to a page.
 */
export function useMarkSectionSeen() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (section: string) => {
      await api.post("/counts/mark-seen", { section });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["counts", "sidebar"] });
    },
  });
}

/**
 * Mark all notifications as read — resets notification badge.
 * Call this when the user opens the notifications page.
 */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post("/notifications/mark-all-read");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["counts", "sidebar"] });
      queryClient.invalidateQueries({ queryKey: ["notifications", "unread"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useOfferCheck(applicationId: string | undefined) {
  return useQuery<{ exists: boolean }>({
    queryKey: ["offer", "check", applicationId],
    queryFn: async () => {
      const res = await api.get<{ exists: boolean }>(`/offers/${applicationId}/check`);
      return res.data;
    },
    enabled: Boolean(applicationId),
  });
}

export async function downloadOfferLetter(applicationId: string) {
  const res = await api.get(`/offers/${applicationId}/download`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = `offer_letter_${applicationId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/* ═══════════════════════════════════════════════════════════
   MUTATION HOOKS — Write data
   ═══════════════════════════════════════════════════════════ */

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: JobCreate) => {
      const res = await api.post<Job>("/jobs/", data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useUpdateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<JobCreate> }) => {
      const res = await api.put<Job>(`/jobs/${id}`, data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useApplyToJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { job_id: string }) => {
      const res = await api.post<Application>("/applications/", data);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useUpdateApplicationStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const res = await api.patch(`/applications/${id}/status`, { status });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useUploadResume() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post<ResumeResponse>("/resumes/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });
}

export function useParseResume() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (resumeId: string) => {
      const res = await api.post(`/resumes/parse/${resumeId}`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["resumes"] });
      qc.invalidateQueries({ queryKey: ["candidate"] });
    },
  });
}

export function useAnalyzeJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const res = await api.post(`/jobs/${jobId}/analyze`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useMatchCandidates() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const res = await api.post(`/jobs/${jobId}/match`);
      return res.data;
    },
    onSuccess: (_data, jobId) => {
      qc.invalidateQueries({ queryKey: ["matches", jobId] });
      qc.invalidateQueries({ queryKey: ["rankings", jobId] });
    },
  });
}

export function useRankCandidates() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const res = await api.post(`/jobs/${jobId}/rank`);
      return res.data;
    },
    onSuccess: (_data, jobId) => {
      qc.invalidateQueries({ queryKey: ["rankings", jobId] });
      qc.invalidateQueries({ queryKey: ["recommendations", jobId] });
    },
  });
}

export function useRunPipeline() {
  return useMutation({
    mutationFn: async (data: { resume_id: string; job_id: string }) => {
      const res = await api.post("/pipeline/run", data);
      return res.data;
    },
  });
}

export function useScheduleInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, data }: { jobId: string; data: Record<string, unknown> }) => {
      const res = await api.post(`/jobs/${jobId}/interviews`, data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interviews"] }),
  });
}

export function useUpdateInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await api.patch(`/interviews/${id}`, data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interviews"] }),
  });
}

export function useCancelInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.delete(`/interviews/${id}`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interviews"] }),
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.patch(`/notifications/${id}/read`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useEvaluateCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, candidateId }: { jobId: string; candidateId: string }) => {
      const res = await api.post(`/jobs/${jobId}/evaluate/${candidateId}`);
      return res.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["evaluations", variables.jobId] });
      qc.invalidateQueries({ queryKey: ["recommendations", variables.jobId] });
    },
  });
}

export function useRecommendCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, candidateId }: { jobId: string; candidateId: string }) => {
      const res = await api.post(`/jobs/${jobId}/recommend/${candidateId}`);
      return res.data;
    },
    onSuccess: (_data, variables) => qc.invalidateQueries({ queryKey: ["recommendations", variables.jobId] }),
  });
}

export function useGenerateCandidateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (candidateId: string) => {
      const res = await api.post(`/reports/candidate/${candidateId}`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
}

export function useGenerateHiringReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const res = await api.post(`/reports/hiring/${jobId}`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
}

export function useGenerateMatchReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const res = await api.post(`/reports/match/${jobId}`);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
}
