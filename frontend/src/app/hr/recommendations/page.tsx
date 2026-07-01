"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs, useRecommendations, useRankings } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { HiringDecision, Job } from "@/types";

function decisionConfig(decision: HiringDecision): { label: string; bg: string; text: string; border: string; icon: string } {
  switch (decision) {
    case "hire":
      return { label: "Hire", bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", icon: "✓" };
    case "consider":
      return { label: "Consider", bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", icon: "◐" };
    case "reject":
      return { label: "Reject", bg: "bg-red-50", text: "text-red-700", border: "border-red-200", icon: "✗" };
    default:
      return { label: decision, bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200", icon: "?" };
  }
}

function atsScoreColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}

function atsScoreLabel(score: number): { text: string; color: string } {
  if (score >= 80) return { text: "Strong Candidate", color: "text-emerald-600" };
  if (score >= 60) return { text: "Needs Review", color: "text-amber-600" };
  return { text: "Below Threshold", color: "text-red-600" };
}

export default function HRRecommendationsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const router = useRouter();
  const { data: jobs, isLoading: jobsLoading } = useJobs();
  const { data: recData, isLoading: recLoading } = useRecommendations(selectedJobId || undefined);
  const { data: rankingsData } = useRankings(selectedJobId || undefined);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const selectedJob: Job | undefined = jobs?.find((j) => j.id === selectedJobId);
  const candidateNameMap = new Map(
    (rankingsData?.rankings ?? []).map((r) => [r.candidate_id, r.candidate_name || `Candidate ${r.candidate_id.slice(0, 8)}`])
  );

  const generateMutation = useMutation({
    mutationFn: (candidateId: string) =>
      api.post(`/jobs/${selectedJobId}/recommend/${candidateId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations", selectedJobId] });
      toast.success("Recommendation regenerated successfully!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to generate recommendation."));
    },
  });

  const recommendations = recData?.recommendations ?? [];

  return (
    <DashboardShell title="Hiring Recommendations" description="AI-powered candidate evaluation with ATS scoring.">
      {/* ATS Score Legend */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-5">
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <label htmlFor="job-select-rec" className="block text-sm font-medium text-slate-700 mb-2">
              Select Job Position
            </label>
            <select
              id="job-select-rec"
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="w-full min-w-[300px] rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
            >
              <option value="">Choose a job…</option>
              {jobsLoading && <option disabled>Loading jobs…</option>}
              {jobs?.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} — {job.department ?? job.location ?? "General"}
                </option>
              ))}
            </select>
          </div>
          <div className="ml-auto flex gap-4 text-xs font-medium">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-emerald-500" />
              <span className="text-slate-600">80+ Hire</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-amber-500" />
              <span className="text-slate-600">60-79 Consider</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-red-500" />
              <span className="text-slate-600">&lt;60 Reject</span>
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      {!selectedJobId ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">Select a Job Position</h3>
          <p className="mt-2 text-sm text-slate-500">Choose a job from the dropdown to view hiring recommendations.</p>
        </div>
      ) : recLoading ? (
        <div className="grid gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="space-y-3">
                  <div className="h-5 w-40 rounded bg-slate-200" />
                  <div className="h-3 w-64 rounded bg-slate-100" />
                </div>
                <div className="h-7 w-20 rounded-full bg-slate-200" />
              </div>
              <div className="mt-4 h-2 w-full rounded bg-slate-100" />
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="h-20 rounded-xl bg-slate-50" />
                <div className="h-20 rounded-xl bg-slate-50" />
              </div>
            </div>
          ))}
        </div>
      ) : recommendations.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No Recommendations Yet</h3>
          <p className="mt-2 text-sm text-slate-500">Generate recommendations from the Candidates page to see them here.</p>
        </div>
      ) : (
        <div className="grid gap-5">
          {recommendations.map((rec) => {
            const dc = decisionConfig(rec.decision);
            const atsScore = Math.round(rec.confidence_score * 100);
            const scoreInfo = atsScoreLabel(atsScore);
            const candidateName = rec.candidate_name ?? candidateNameMap.get(rec.candidate_id) ?? `Candidate`;
            return (
              <div key={rec.id} className={`rounded-lg border bg-white shadow-sm p-6 transition hover:shadow-md ${dc.border}`}>
                {/* Header */}
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-slate-900">{candidateName}</p>
                    {rec.summary && (
                      <p className="text-sm text-slate-600">{rec.summary}</p>
                    )}
                  </div>
                  <span className={`inline-flex items-center gap-1.5 self-start rounded-full px-3.5 py-1.5 text-sm font-bold ${dc.bg} ${dc.text}`}>
                    <span>{dc.icon}</span>
                    {dc.label}
                  </span>
                </div>

                {/* ATS Score Bar */}
                <div className="mt-5">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-700">ATS Score</span>
                      <span className={`text-xs font-medium ${scoreInfo.color}`}>{scoreInfo.text}</span>
                    </div>
                    <span className={`text-2xl font-bold ${scoreInfo.color}`}>{atsScore}<span className="text-sm text-slate-400">/100</span></span>
                  </div>
                  <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${atsScoreColor(atsScore)}`}
                      style={{ width: `${atsScore}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-slate-400">0</span>
                    <span className="text-[10px] text-red-400">60</span>
                    <span className="text-[10px] text-amber-400">80</span>
                    <span className="text-[10px] text-slate-400">100</span>
                  </div>
                </div>

                {/* Strengths & Weaknesses */}
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  {rec.strengths && rec.strengths.length > 0 && (
                    <div className="rounded-xl bg-emerald-50/50 border border-emerald-100 p-4">
                      <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-2">Strengths</p>
                      <ul className="space-y-1.5">
                        {rec.strengths.map((s, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                            <svg className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                            </svg>
                            <span><span className="font-medium">{s.area}:</span> {s.detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {rec.weaknesses && rec.weaknesses.length > 0 && (
                    <div className="rounded-xl bg-red-50/50 border border-red-100 p-4">
                      <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-2">Areas for Improvement</p>
                      <ul className="space-y-1.5">
                        {rec.weaknesses.map((w, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                            <svg className="h-4 w-4 text-red-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                            </svg>
                            <span><span className="font-medium">{w.area}:</span> {w.detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Reasoning */}
                {rec.reasoning && rec.reasoning !== "Recommendation could not be generated." && (
                  <div className="mt-4 rounded-xl bg-slate-50 px-4 py-3">
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Reasoning</p>
                    <p className="text-sm text-slate-600 leading-relaxed">{rec.reasoning}</p>
                  </div>
                )}

                {/* Risk Assessment */}
                {rec.risk_assessment && (
                  <div className="mt-3 rounded-xl bg-blue-50/50 border border-blue-100 px-4 py-3">
                    <p className="text-xs font-medium text-blue-600 uppercase tracking-wider mb-1">Risk Assessment</p>
                    <p className="text-sm text-slate-600">{rec.risk_assessment}</p>
                  </div>
                )}

                <div className="mt-5 flex justify-end gap-2">
                  {rec.decision === "hire" && (
                    <button
                      onClick={() => {
                        const name = candidateNameMap.get(rec.candidate_id) ?? `Candidate`;
                        router.push(
                          `/hr/candidates?job=${selectedJobId}&schedule=${rec.candidate_id}&name=${encodeURIComponent(name)}`
                        );
                      }}
                      className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-violet-700"
                    >
                      Schedule Interview
                    </button>
                  )}
                  {rec.decision === "consider" && (
                    <button
                      onClick={() => {
                        const name = candidateNameMap.get(rec.candidate_id) ?? `Candidate`;
                        router.push(
                          `/hr/candidates?job=${selectedJobId}&schedule=${rec.candidate_id}&name=${encodeURIComponent(name)}`
                        );
                      }}
                      className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-amber-600"
                    >
                      Schedule Interview
                    </button>
                  )}
                  <button
                    onClick={() => generateMutation.mutate(rec.candidate_id)}
                    disabled={generateMutation.isPending}
                    className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                  >
                    {generateMutation.isPending ? "Generating…" : "Regenerate"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </DashboardShell>
  );
}
