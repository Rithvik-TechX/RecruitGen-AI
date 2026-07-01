"use client";

import { useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs, useRankings, useRankCandidates } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import type { Job, CandidateRanking } from "@/types";

function ScoreBar({ score, color }: { score: number; color: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-medium text-slate-600 w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function RecruiterRankingsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string>("");

  const jobsQuery = useJobs();
  const rankingsQuery = useRankings(selectedJobId || undefined);
  const rankMutation = useRankCandidates();
  const { toast, dismiss } = useToast();

  const jobs: Job[] = jobsQuery.data ?? [];
  const rankings: CandidateRanking[] = rankingsQuery.data?.rankings ?? [];

  const handleRunRanking = () => {
    if (!selectedJobId) { toast.warning("Please select a job first."); return; }
    const toastId = toast.loading("Running AI candidate ranking...");
    rankMutation.mutate(selectedJobId, {
      onSuccess: (data) => {
        const count = data?.rankings?.length ?? data?.total_count ?? 0;
        dismiss(toastId);
        toast.success(`Ranking completed! ${count} candidates ranked.`);
      },
      onError: (error) => {
        dismiss(toastId);
        toast.error(getApiError(error, "Ranking failed."));
      },
    });
  };

  return (
    <DashboardShell
      title="AI Rankings"
      description="View AI-powered candidate rankings by job position."
      actions={
        <button
          onClick={handleRunRanking}
          disabled={!selectedJobId || rankMutation.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {rankMutation.isPending ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Ranking...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Run AI Ranking
            </>
          )}
        </button>
      }
    >
      {/* ── Job Selector ───────────────────────────── */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-5">
        <label className="block text-sm font-medium text-slate-700 mb-2">Select a Job Position</label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full max-w-md rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
        >
          <option value="">Choose a job to view rankings...</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>
              {j.title} — {j.department ?? "General"}
            </option>
          ))}
        </select>
      </div>


      {/* ── Rankings Content ───────────────────────── */}
      {!selectedJobId ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">Select a job</h3>
          <p className="mt-2 text-sm text-slate-500">
            Choose a job position above to view candidate rankings.
          </p>
        </div>
      ) : rankingsQuery.isLoading ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-4">
                <div className="h-8 w-8 rounded-full bg-slate-200" />
                <div className="h-4 w-1/4 rounded bg-slate-200" />
                <div className="h-4 w-1/6 rounded bg-slate-100" />
                <div className="h-4 w-1/6 rounded bg-slate-100" />
                <div className="h-4 w-1/6 rounded bg-slate-100" />
                <div className="h-4 w-1/6 rounded bg-slate-200" />
              </div>
            ))}
          </div>
        </div>
      ) : rankings.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No rankings yet</h3>
          <p className="mt-2 text-sm text-slate-500">
            Click &quot;Run AI Ranking&quot; to generate candidate rankings for this position.
          </p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-5">
              <p className="text-sm text-slate-500">Total Candidates</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">{rankings.length}</p>
            </div>
            <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-5">
              <p className="text-sm text-slate-500">Top Score</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-600">
                {Math.round(Math.max(...rankings.map((r) => r.final_score)) * 100)}%
              </p>
            </div>
            <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-5">
              <p className="text-sm text-slate-500">Average Score</p>
              <p className="mt-1 text-2xl font-semibold text-blue-600">
                {Math.round(
                  (rankings.reduce((s, r) => s + r.final_score, 0) / rankings.length) * 100,
                )}%
              </p>
            </div>
          </div>

          {/* Rankings Table */}
          <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Rank
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Candidate
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Final Score
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Skills
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Experience
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Education
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rankings
                    .sort((a, b) => a.rank_position - b.rank_position)
                    .map((ranking) => (
                      <tr key={ranking.candidate_id} className="hover:bg-slate-50/50 transition">
                        <td className="px-6 py-4">
                          <div
                            className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                              ranking.rank_position === 1
                                ? "bg-amber-100 text-amber-700"
                                : ranking.rank_position === 2
                                  ? "bg-slate-200 text-slate-700"
                                  : ranking.rank_position === 3
                                    ? "bg-orange-100 text-orange-700"
                                    : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {ranking.rank_position}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-blue-600 text-xs font-semibold">
                              {(ranking.candidate_name || "?")[0].toUpperCase()}
                            </div>
                            <span className="text-sm font-medium text-slate-900">
                              {ranking.candidate_name || `Candidate ${ranking.candidate_id.slice(0, 8)}`}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-2.5 w-24 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-blue-600 transition-all duration-500"
                                style={{ width: `${Math.round(ranking.final_score * 100)}%` }}
                              />
                            </div>
                            <span className="text-sm font-semibold text-slate-900">
                              {Math.round(ranking.final_score * 100)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <ScoreBar score={ranking.skill_score} color="#8b5cf6" />
                        </td>
                        <td className="px-6 py-4">
                          <ScoreBar score={ranking.experience_score} color="#0ea5e9" />
                        </td>
                        <td className="px-6 py-4">
                          <ScoreBar score={ranking.education_score} color="#10b981" />
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

    </DashboardShell>
  );
}
