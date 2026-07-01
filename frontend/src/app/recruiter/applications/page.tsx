"use client";

import { useState, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { AIStatusIndicator } from "@/components/ui/AIStatusIndicator";
import { useJobs, useMatchCandidates, useMatches, useUpdateApplicationStatus, useMarkSectionSeen } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Application, ApplicationStatus, Job, CandidateMatch } from "@/types";

const STATUS_TABS: Array<{ label: string; value: ApplicationStatus | "all" }> = [
  { label: "All", value: "all" },
  { label: "Applied", value: "applied" },
  { label: "Screened", value: "screened" },
  { label: "Shortlisted", value: "shortlisted" },
  { label: "Interview", value: "interview_scheduled" },
  { label: "Rejected", value: "rejected" },
  { label: "Selected", value: "selected" },
];

function statusBadge(status: ApplicationStatus) {
  const map: Record<ApplicationStatus, string> = {
    applied: "bg-slate-100 text-slate-600",
    screened: "bg-blue-50 text-blue-700",
    shortlisted: "bg-emerald-50 text-emerald-700",
    interview_scheduled: "bg-violet-50 text-violet-700",
    interview_completed: "bg-sky-50 text-sky-700",
    rejected: "bg-red-50 text-red-600",
    selected: "bg-teal-50 text-teal-700",
  };
  return map[status] ?? "bg-slate-100 text-slate-600";
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-500 w-16">{label}</span>
      <div className="h-1.5 w-16 rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-600 w-8">{pct}%</span>
    </div>
  );
}

export default function RecruiterApplicationsPage() {
  const [activeTab, setActiveTab] = useState<ApplicationStatus | "all">("all");
  const [selectedJobId, setSelectedJobId] = useState<string>("");

  const jobsQuery = useJobs();
  const queryClient = useQueryClient();
  const { toast, dismiss } = useToast();
  const statusMutation = useUpdateApplicationStatus();
  const matchMutation = useMatchCandidates();
  const markSeen = useMarkSectionSeen();
  useEffect(() => { markSeen.mutate("recruiter_applications"); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch all applications (for "all" view)
  const allApplicationsQuery = useQuery<Application[]>({
    queryKey: ["applications", "all"],
    queryFn: async () => {
      const res = await api.get<Application[]>("/applications/");
      return res.data;
    },
  });

  // Fetch applications filtered by job (when a job is selected)
  const jobApplicationsQuery = useQuery<Application[]>({
    queryKey: ["applications", "job", selectedJobId],
    queryFn: async () => {
      const res = await api.get<Application[]>(`/jobs/${selectedJobId}/applications`);
      return res.data;
    },
    enabled: Boolean(selectedJobId),
  });

  // Fetch match results for the selected job
  const matchesQuery = useMatches(selectedJobId || undefined);

  const jobs: Job[] = jobsQuery.data ?? [];
  const matches: CandidateMatch[] = matchesQuery.data?.matches ?? [];

  // Build a map of candidate_id -> match data for inline display
  const matchMap = new Map(matches.map((m) => [m.candidate_id, m]));

  // Determine which applications to show
  const rawApps = selectedJobId
    ? (jobApplicationsQuery.data ?? [])
    : (allApplicationsQuery.data ?? []);

  const applications =
    activeTab === "all" ? rawApps : rawApps.filter((a) => a.status === activeTab);

  const isLoading = selectedJobId ? jobApplicationsQuery.isLoading : allApplicationsQuery.isLoading;

  // Job name lookup (fallback if job_title not in response)
  const jobMap = new Map(jobs.map((j) => [j.id, j.title]));

  // Handle matching
  const handleRunMatching = () => {
    if (!selectedJobId) { toast.warning("Please select a job first."); return; }
    const toastId = toast.loading("Running AI matching...");
    matchMutation.mutate(selectedJobId, {
      onSuccess: (data) => {
        const count = data?.matches?.length ?? data?.total_count ?? 0;
        dismiss(toastId);
        toast.success(`Matching completed! ${count} candidates matched.`);
        queryClient.invalidateQueries({ queryKey: ["applications"] });
        queryClient.invalidateQueries({ queryKey: ["matches", selectedJobId] });
      },
      onError: (error) => {
        dismiss(toastId);
        toast.error(getApiError(error, "Matching failed."));
      },
    });
  };

  return (
    <DashboardShell
      title="Application Management"
      description="Review and process candidate applications across all positions."
      actions={
        <div className="flex items-center gap-3">
          <AIStatusIndicator />
          <select
            value={selectedJobId}
            onChange={(e) => {
              setSelectedJobId(e.target.value);
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Jobs</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </select>
          <button
            onClick={handleRunMatching}
            disabled={!selectedJobId || matchMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {matchMutation.isPending ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Matching...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Run Matching
              </>
            )}
          </button>
        </div>
      }
    >
      {/* ── Status Filter Tabs ──────────────────── */}
      <div className="mb-6 flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              activeTab === tab.value
                ? "bg-blue-600 text-white shadow-sm"
                : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {tab.label}
            {tab.value === "all" && ` (${rawApps.length})`}
          </button>
        ))}
      </div>

      {/* ── Match Results Summary (when job selected & matches exist) ── */}
      {selectedJobId && matches.length > 0 && (
        <div className="mb-6 rounded-lg border border-blue-100 bg-blue-50/50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <h3 className="text-sm font-semibold text-blue-900">
              AI Match Results &mdash; {matches.length} candidates matched
            </h3>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg bg-white p-3 shadow-sm border border-blue-100">
              <p className="text-xs text-slate-500">Top Score</p>
              <p className="text-lg font-bold text-emerald-600">
                {Math.round(Math.max(...matches.map((m) => m.overall_match_score)) * 100)}%
              </p>
            </div>
            <div className="rounded-lg bg-white p-3 shadow-sm border border-blue-100">
              <p className="text-xs text-slate-500">Avg Score</p>
              <p className="text-lg font-bold text-blue-600">
                {Math.round(
                  (matches.reduce((s, m) => s + m.overall_match_score, 0) / matches.length) * 100
                )}%
              </p>
            </div>
            <div className="rounded-lg bg-white p-3 shadow-sm border border-blue-100">
              <p className="text-xs text-slate-500">Candidates</p>
              <p className="text-lg font-bold text-slate-800">{matches.length}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Applications Table ──────────────────── */}
      {isLoading ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-4">
                <div className="h-4 w-1/4 rounded bg-slate-200" />
                <div className="h-4 w-1/4 rounded bg-slate-100" />
                <div className="h-4 w-1/6 rounded bg-slate-100" />
                <div className="h-4 w-1/6 rounded bg-slate-100" />
                <div className="h-4 w-1/6 rounded bg-slate-200" />
              </div>
            ))}
          </div>
        </div>
      ) : applications.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No applications found</h3>
          <p className="mt-2 text-sm text-slate-500">
            {activeTab === "all"
              ? "Applications will appear here once candidates apply."
              : `No applications with "${activeTab}" status.`}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Candidate
                  </th>
                  <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Job Title
                  </th>
                  <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Status
                  </th>
                  {selectedJobId && matches.length > 0 && (
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Match Score
                    </th>
                  )}
                  <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Applied
                  </th>
                  <th className="px-6 py-3.5 text-right text-xs font-medium uppercase tracking-wider text-slate-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications.map((app) => {
                  const candidateMatch = app.candidate_profile_id
                    ? matchMap.get(app.candidate_profile_id)
                    : undefined;
                  const displayName = app.candidate_name || `Candidate ${app.candidate_id.slice(0, 8)}`;
                  const jobTitle = app.job_title || jobMap.get(app.job_id) || app.job_id.slice(0, 8);

                  return (
                    <tr key={app.id} className="hover:bg-slate-50/50 transition">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-blue-600 text-sm font-semibold">
                            {displayName[0].toUpperCase()}
                          </div>
                          <div>
                            <span className="text-sm font-medium text-slate-900 block">
                              {displayName}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">
                        {jobTitle}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadge(app.status)}`}>
                          {app.status.replace("_", " ")}
                        </span>
                      </td>
                      {selectedJobId && matches.length > 0 && (
                        <td className="px-6 py-4">
                          {candidateMatch ? (
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <div className="h-2 w-20 rounded-full bg-slate-100 overflow-hidden">
                                  <div
                                    className="h-full rounded-full bg-blue-600 transition-all duration-500"
                                    style={{ width: `${Math.round(candidateMatch.overall_match_score * 100)}%` }}
                                  />
                                </div>
                                <span className="text-sm font-semibold text-blue-700">
                                  {Math.round(candidateMatch.overall_match_score * 100)}%
                                </span>
                              </div>
                              <div className="flex gap-3">
                                <ScoreBar score={candidateMatch.skill_match_score} label="Skills" />
                                <ScoreBar score={candidateMatch.experience_match_score} label="Exp" />
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No match data</span>
                          )}
                        </td>
                      )}
                      <td className="px-6 py-4 text-sm text-slate-500">
                        {new Date(app.applied_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          {/* Show only valid next-step buttons based on current status */}
                          {app.status === "applied" && (
                            <button
                              onClick={() => {
                                statusMutation.mutate({ id: app.id, status: "screened" }, {
                                  onSuccess: () => toast.success(`Candidate ${displayName} screened.`),
                                  onError: (err) => toast.error(getApiError(err, "Failed to screen candidate.")),
                                });
                              }}
                              disabled={statusMutation.isPending}
                              className="rounded-lg px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition disabled:opacity-40"
                            >
                              Screen
                            </button>
                          )}
                          {app.status === "screened" && (
                            <button
                              onClick={() => {
                                statusMutation.mutate({ id: app.id, status: "shortlisted" }, {
                                  onSuccess: () => toast.success(`Candidate ${displayName} shortlisted.`),
                                  onError: (err) => toast.error(getApiError(err, "Failed to shortlist candidate.")),
                                });
                              }}
                              disabled={statusMutation.isPending}
                              className="rounded-lg px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition disabled:opacity-40"
                            >
                              Shortlist
                            </button>
                          )}
                          {!["rejected", "selected"].includes(app.status) && (
                            <button
                              onClick={() => {
                                statusMutation.mutate({ id: app.id, status: "rejected" }, {
                                  onSuccess: () => toast.success(`Candidate ${displayName} rejected.`),
                                  onError: (err) => toast.error(getApiError(err, "Failed to reject candidate.")),
                                });
                              }}
                              disabled={statusMutation.isPending}
                              className="rounded-lg px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 transition disabled:opacity-40"
                            >
                              Reject
                            </button>
                          )}
                          {["rejected", "selected"].includes(app.status) && (
                            <span className="text-xs text-slate-400 italic">Final</span>
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

    </DashboardShell>
  );
}
