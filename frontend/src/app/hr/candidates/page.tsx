"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { AIStatusIndicator } from "@/components/ui/AIStatusIndicator";
import { useHRCandidatePipeline, useJobs, useMarkSectionSeen } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError, validateMeetingLink } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ApplicationStatus, InterviewType, Job } from "@/types";

function statusBadge(status: ApplicationStatus): string {
  const styles: Record<ApplicationStatus, string> = {
    applied: "bg-slate-100 text-slate-700",
    screened: "bg-blue-50 text-blue-700",
    shortlisted: "bg-emerald-50 text-emerald-700",
    interview_scheduled: "bg-violet-50 text-violet-700",
    interview_completed: "bg-indigo-50 text-indigo-700",
    selected: "bg-teal-50 text-teal-700",
    rejected: "bg-red-50 text-red-700",
  };
  return styles[status];
}

/* ── Schedule Interview Modal State ────────────────────── */
interface ScheduleTarget {
  candidate_id: string;
  candidate_name: string;
  job_id: string;
  job_title: string;
}

interface ScheduleForm {
  scheduled_at: string;
  duration_minutes: number;
  interview_type: InterviewType;
  meeting_link: string;
  notes: string;
}

const defaultForm: ScheduleForm = {
  scheduled_at: "",
  duration_minutes: 30,
  interview_type: "video",
  meeting_link: "",
  notes: "",
};

export default function HRCandidatesPage() {
  return (
    <Suspense>
      <HRCandidatesContent />
    </Suspense>
  );
}

function HRCandidatesContent() {
  const searchParams = useSearchParams();
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [scheduleTarget, setScheduleTarget] = useState<ScheduleTarget | null>(null);
  const [form, setForm] = useState<ScheduleForm>(defaultForm);
  const [urlParamsHandled, setUrlParamsHandled] = useState(false);

  const { data: jobs, isLoading: jobsLoading } = useJobs();
  const { data: pipeline, isLoading: pipelineLoading } = useHRCandidatePipeline(selectedJobId || undefined);
  const queryClient = useQueryClient();
  const { toast, dismiss } = useToast();
  const markSeen = useMarkSectionSeen();
  useEffect(() => { markSeen.mutate("hr_candidates"); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedJob: Job | undefined = jobs?.find((j) => j.id === selectedJobId);

  // Auto-open schedule modal from URL params (e.g. from Recommendations page)
  useEffect(() => {
    if (urlParamsHandled || !jobs) return;
    const jobParam = searchParams.get("job");
    const scheduleParam = searchParams.get("schedule");
    const nameParam = searchParams.get("name");
    if (jobParam && scheduleParam) {
      window.setTimeout(() => {
      setSelectedJobId(jobParam);
      const job = jobs.find((j) => j.id === jobParam);
      if (job) {
        setScheduleTarget({
          candidate_id: scheduleParam,
          candidate_name: nameParam || `Candidate ${scheduleParam.slice(0, 8)}`,
          job_id: jobParam,
          job_title: `${job.title} — ${job.department ?? job.location ?? "General"}`,
        });
        setForm(defaultForm);
      }
      setUrlParamsHandled(true);
      }, 0);
    }
  }, [searchParams, jobs, urlParamsHandled]);

  const evaluateMutation = useMutation({
    mutationFn: (candidateId: string) =>
      api.post(`/jobs/${selectedJobId}/evaluate/${candidateId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", "pipeline"] });
      toast.success("Candidate evaluation completed!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to evaluate candidate."));
    },
  });

  const recommendMutation = useMutation({
    mutationFn: (candidateId: string) =>
      api.post(`/jobs/${selectedJobId}/recommend/${candidateId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations", selectedJobId] });
      toast.success("Recommendation generated successfully!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to generate recommendation."));
    },
  });

  const scheduleMutation = useMutation({
    mutationFn: (payload: ScheduleForm & { candidate_id: string; job_id: string }) =>
      api.post(`/jobs/${payload.job_id}/interviews`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      queryClient.invalidateQueries({ queryKey: ["applications", "pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Interview scheduled successfully!");
      setScheduleTarget(null);
      setForm(defaultForm);
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to schedule interview."));
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ appId, newStatus }: { appId: string; newStatus: string }) =>
      api.patch(`/applications/${appId}/status`, { status: newStatus }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", "pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to update status."));
    },
  });

  const [outcomeTarget, setOutcomeTarget] = useState<{ appId: string; candidateName: string; jobTitle: string } | null>(null);
  const [outcomeDecision, setOutcomeDecision] = useState<"selected" | "rejected">("selected");
  const [outcomeComments, setOutcomeComments] = useState("");

  const handleOutcomeSubmit = () => {
    if (!outcomeTarget) return;
    const toastId = toast.loading(outcomeDecision === "selected" ? "Hiring candidate..." : "Processing rejection...");
    statusMutation.mutate(
      { appId: outcomeTarget.appId, newStatus: outcomeDecision },
      {
        onSuccess: () => {
          dismiss(toastId);
          toast.success(outcomeDecision === "selected" ? "Candidate hired successfully!" : "Candidate rejected.");
          if (outcomeDecision === "selected") {
            api.post(`/offers/${outcomeTarget.appId}/generate`).catch(() => {});
          }
          setOutcomeTarget(null);
          setOutcomeComments("");
        },
        onSettled: () => dismiss(toastId),
      }
    );
  };

  const candidates = pipeline ?? [];

  const openScheduleModal = (candidateId: string, candidateName: string) => {
    if (!selectedJob) return;
    setScheduleTarget({
      candidate_id: candidateId,
      candidate_name: candidateName || `Candidate ${candidateId.slice(0, 8)}`,
      job_id: selectedJob.id,
      job_title: `${selectedJob.title} — ${selectedJob.department ?? selectedJob.location ?? "General"}`,
    });
    setForm(defaultForm);
  };

  const handleScheduleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!scheduleTarget) return;
    if (!form.scheduled_at) {
      toast.warning("Please select a date and time.");
      return;
    }
    const linkError = validateMeetingLink(form.meeting_link);
    if (linkError) {
      toast.warning(linkError);
      return;
    }
    const toastId = toast.loading("Scheduling interview…");
    scheduleMutation.mutate(
      {
        ...form,
        candidate_id: scheduleTarget.candidate_id,
        job_id: scheduleTarget.job_id,
      },
      {
        onSettled: () => dismiss(toastId),
      },
    );
  };

  return (
    <DashboardShell title="Candidate Pipeline" description="Review candidate rankings and match scores across open roles.">
      <div className="mb-4 flex justify-end">
        <AIStatusIndicator />
      </div>
      {/* Job Selector */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
        <label htmlFor="job-select" className="block text-sm font-medium text-slate-700 mb-2">
          Select Job Position
        </label>
        <select
          id="job-select"
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full max-w-md rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
        >
          <option value="">All organization jobs</option>
          {jobsLoading && <option disabled>Loading jobs…</option>}
          {jobs?.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title} — {job.department ?? job.location ?? "General"}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {pipelineLoading ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
          <div className="p-6">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-4 py-4 border-b border-slate-100 last:border-0">
                <div className="h-4 w-32 rounded bg-slate-200" />
                <div className="h-4 w-16 rounded bg-slate-200" />
                <div className="h-4 w-16 rounded bg-slate-200" />
                <div className="h-4 w-20 rounded bg-slate-200" />
                <div className="flex-1" />
                <div className="h-8 w-20 rounded bg-slate-200" />
              </div>
            ))}
          </div>
        </div>
      ) : candidates.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No Candidates Yet</h3>
          <p className="mt-2 text-sm text-slate-500">Screened, shortlisted, and interview-stage applications will appear here automatically.</p>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-slate-200 px-6 py-4">
            <h3 className="text-lg font-semibold text-slate-900">HR Candidate Pipeline</h3>
            <p className="mt-1 text-sm text-slate-500">{candidates.length} active candidate{candidates.length !== 1 ? "s" : ""} in the pipeline</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Rank</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Candidate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Match Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Skill Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {candidates.map((candidate) => {
                  const displayName = candidate.candidate_name || `Candidate ${candidate.candidate_id.slice(0, 8)}`;
                  const profileId = candidate.candidate_profile_id;
                  const matchScore = candidate.overall_match_score;
                  const skillScore = candidate.skill_match_score;
                  return (
                    <tr key={candidate.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-blue-700">
                          {candidate.rank_position ?? "—"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-blue-600 text-xs font-semibold">
                            {displayName[0].toUpperCase()}
                          </div>
                          <p className="font-medium text-slate-900">{displayName}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-20 rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full rounded-full bg-blue-600" style={{ width: `${Math.round((matchScore ?? 0) * 100)}%` }} />
                          </div>
                          <span className="text-sm font-medium text-slate-700">
                            {matchScore == null ? "Not run" : `${Math.round(matchScore * 100)}%`}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-20 rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.round((skillScore ?? 0) * 100)}%` }} />
                          </div>
                          <span className="text-sm font-medium text-slate-700">
                            {skillScore == null ? "Not run" : `${Math.round(skillScore * 100)}%`}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusBadge(candidate.status)}`}>
                          {candidate.status.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-2">
                          {(candidate.status === "screened" || candidate.status === "shortlisted" || candidate.status === "applied") && (
                            <>
                              <button
                                onClick={() => profileId && evaluateMutation.mutate(profileId)}
                                disabled={evaluateMutation.isPending || !profileId || !selectedJobId}
                                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                              >
                                {evaluateMutation.isPending ? "\u2026" : "Evaluate"}
                              </button>
                              <button
                                onClick={() => profileId && recommendMutation.mutate(profileId)}
                                disabled={recommendMutation.isPending || !profileId || !selectedJobId}
                                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                              >
                                {recommendMutation.isPending ? "\u2026" : "Recommend"}
                              </button>
                              <button
                                onClick={() => profileId && openScheduleModal(profileId, displayName)}
                                disabled={!profileId || !selectedJobId}
                                className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-violet-700 disabled:opacity-50"
                              >
                                Schedule
                              </button>
                            </>
                          )}
                          {candidate.status === "interview_scheduled" && (
                            <>
                              <button
                                onClick={async () => {
                                  if (!profileId || !candidate.job_id) return;
                                  try {
                                    const res = await api.get("/interviews/by-application", {
                                      params: { candidate_profile_id: profileId, job_id: candidate.job_id },
                                    });
                                    const meetLink = res.data?.meeting_link;
                                    if (meetLink) {
                                      window.open(meetLink, "_blank");
                                    } else {
                                      toast.warning("No meeting link found for this interview.");
                                    }
                                  } catch {
                                    toast.error("Failed to fetch interview details.");
                                  }
                                }}
                                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-700"
                              >
                                Start Interview
                              </button>
                              <button
                                onClick={() => {
                                  const jt = selectedJob ? selectedJob.title : "this position";
                                  setOutcomeTarget({ appId: candidate.id, candidateName: displayName, jobTitle: jt });
                                  setOutcomeDecision("selected");
                                  setOutcomeComments("");
                                }}
                                className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-indigo-700"
                              >
                                Interview Completed
                              </button>
                            </>
                          )}
                          {candidate.status === "interview_completed" && (
                            <>
                              <button
                                onClick={() => {
                                  const jt = selectedJob ? selectedJob.title : "this position";
                                  setOutcomeTarget({ appId: candidate.id, candidateName: displayName, jobTitle: jt });
                                  setOutcomeDecision("selected");
                                  setOutcomeComments("");
                                }}
                                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-emerald-700"
                              >
                                Hire
                              </button>
                              <button
                                onClick={() => {
                                  const jt = selectedJob ? selectedJob.title : "this position";
                                  setOutcomeTarget({ appId: candidate.id, candidateName: displayName, jobTitle: jt });
                                  setOutcomeDecision("rejected");
                                  setOutcomeComments("");
                                }}
                                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-red-700"
                              >
                                Reject
                              </button>
                            </>
                          )}
                          {candidate.status === "selected" && (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                              ✓ Hired
                            </span>
                          )}
                          {candidate.status === "rejected" && (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700">
                              ✗ Rejected
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Schedule Interview Modal ─────────────────────── */}
      {scheduleTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Schedule Interview</h3>
              <button
                onClick={() => setScheduleTarget(null)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleScheduleSubmit} className="p-6 space-y-4">
              {/* Read-only Candidate & Job Info */}
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 space-y-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-bold">
                    {scheduleTarget.candidate_name[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{scheduleTarget.candidate_name}</p>
                    <p className="text-xs text-slate-500">{scheduleTarget.job_title}</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Date & Time</label>
                  <input
                    type="datetime-local"
                    required
                    value={form.scheduled_at}
                    onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Duration</label>
                  <select
                    value={form.duration_minutes}
                    onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })}
                    className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  >
                    <option value={15}>15 minutes</option>
                    <option value={30}>30 minutes</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>60 minutes</option>
                    <option value={90}>90 minutes</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Interview Type</label>
                <select
                  value={form.interview_type}
                  onChange={(e) => setForm({ ...form, interview_type: e.target.value as InterviewType })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                >
                  <option value="phone">Phone</option>
                  <option value="video">Video</option>
                  <option value="onsite">Onsite</option>
                  <option value="technical">Technical</option>
                  <option value="hr">HR</option>
                  <option value="panel">Panel</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Meeting Link</label>
                <input
                  type="url"
                  value={form.meeting_link}
                  onChange={(e) => setForm({ ...form, meeting_link: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="https://meet.google.com/..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={3}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition resize-none"
                  placeholder="Any additional notes…"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setScheduleTarget(null)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scheduleMutation.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {scheduleMutation.isPending ? "Scheduling…" : "Schedule Interview"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Interview Outcome Modal */}
      {outcomeTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Interview Outcome</h3>
              <button onClick={() => setOutcomeTarget(null)} className="text-slate-400 hover:text-slate-600 transition">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-5">
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                <p className="text-sm font-semibold text-slate-900">{outcomeTarget.candidateName}</p>
                <p className="text-xs text-slate-500 mt-0.5">{outcomeTarget.jobTitle}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Decision</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setOutcomeDecision("selected")}
                    className={`flex items-center justify-center gap-2 rounded-xl border-2 px-4 py-3 text-sm font-medium transition ${outcomeDecision === "selected" ? "border-emerald-500 bg-emerald-50 text-emerald-700" : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"}`}
                  >
                    Hire
                  </button>
                  <button
                    type="button"
                    onClick={() => setOutcomeDecision("rejected")}
                    className={`flex items-center justify-center gap-2 rounded-xl border-2 px-4 py-3 text-sm font-medium transition ${outcomeDecision === "rejected" ? "border-red-500 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"}`}
                  >
                    Reject
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Comments</label>
                <textarea
                  value={outcomeComments}
                  onChange={(e) => setOutcomeComments(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition resize-none"
                  placeholder="Add any notes about the interview..."
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-2">
                <button type="button" onClick={() => setOutcomeTarget(null)} className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
                  Cancel
                </button>
                <button
                  onClick={() => {
                    const currentStatus = candidates.find(c => c.id === outcomeTarget.appId)?.status;
                    if (currentStatus === "interview_scheduled") {
                      statusMutation.mutate(
                        { appId: outcomeTarget.appId, newStatus: "interview_completed" },
                        { onSuccess: () => handleOutcomeSubmit() }
                      );
                    } else {
                      handleOutcomeSubmit();
                    }
                  }}
                  disabled={statusMutation.isPending}
                  className={`rounded-lg px-4 py-2.5 text-sm font-medium text-white transition disabled:opacity-50 ${outcomeDecision === "selected" ? "bg-emerald-600 hover:bg-emerald-700" : "bg-red-600 hover:bg-red-700"}`}
                >
                  {statusMutation.isPending ? "Processing..." : outcomeDecision === "selected" ? "Confirm Hire" : "Confirm Rejection"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
