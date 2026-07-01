"use client";

import { useMemo } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useAnalyticsDashboard, useHRCandidatePipeline } from "@/lib/hooks";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function stageBadgeColor(stage: string): string {
  switch (stage) {
    case "Applied": return "bg-gray-100 text-gray-700";
    case "Screened": return "bg-blue-50 text-blue-700";
    case "Interviewed": return "bg-indigo-50 text-indigo-700";
    case "Evaluated": return "bg-amber-50 text-amber-700";
    case "Offered": return "bg-emerald-50 text-emerald-700";
    case "Hired": return "bg-green-50 text-green-700";
    default: return "bg-gray-100 text-gray-700";
  }
}

function stageDotColor(stage: string): string {
  switch (stage) {
    case "Applied": return "bg-gray-400";
    case "Screened": return "bg-blue-500";
    case "Interviewed": return "bg-indigo-500";
    case "Evaluated": return "bg-amber-500";
    case "Offered": return "bg-emerald-500";
    case "Hired": return "bg-green-500";
    default: return "bg-gray-400";
  }
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 shadow-sm">
      <p className="text-xs text-[#6b7280]">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-[#111827]">{payload[0].value} candidates</p>
    </div>
  );
}

function KPICard({ label, value, caption }: { label: string; value: number | string; caption: string }) {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
      <p className="text-sm text-[#6b7280]">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-[#111827]">{value}</p>
      <p className="mt-1 text-xs text-[#9ca3af]">{caption}</p>
    </div>
  );
}

export default function HRDashboardPage() {
  const { data, isLoading } = useAnalyticsDashboard();
  const { data: pipelineCandidates, isLoading: pipelineLoading } = useHRCandidatePipeline();

  const kpi = useMemo(() => {
    const stats = data?.stats;
    const pipeline = data?.pipeline;
    return {
      totalCandidates: stats?.total_candidates ?? 0,
      interviewsToday: pipeline?.interviews_this_week ?? 0,
      pendingEvaluations: pipeline?.pending_reviews ?? 0,
      recommendationsMade: stats?.shortlisted ?? 0,
    };
  }, [data]);

  const funnelData = useMemo(() => {
    const stats = data?.stats;
    return [
      { stage: "Applications", count: stats?.total_applications ?? 0 },
      { stage: "Pipeline", count: pipelineCandidates?.length ?? 0 },
      { stage: "Shortlisted", count: stats?.shortlisted ?? 0 },
      { stage: "Interviews", count: stats?.interviews_scheduled ?? 0 },
      { stage: "Selected", count: Math.round((stats?.hiring_rate ?? 0) / 100 * (stats?.total_applications ?? 0)) },
    ];
  }, [data, pipelineCandidates]);

  if (isLoading || pipelineLoading) {
    return (
      <DashboardShell title="HR Dashboard" description="Track hiring velocity, candidate outcomes, and interview workflow.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
              <div className="animate-pulse space-y-3">
                <div className="h-3.5 w-24 rounded bg-[#f3f4f6]" />
                <div className="h-7 w-16 rounded bg-[#f3f4f6]" />
                <div className="h-3 w-32 rounded bg-[#f3f4f6]" />
              </div>
            </div>
          ))}
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="HR Dashboard" description="Track hiring velocity, candidate outcomes, and interview workflow.">
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard label="Total Candidates" value={kpi.totalCandidates} caption="Active profiles in pipeline" />
        <KPICard label="Interviews Today" value={kpi.interviewsToday} caption="Scheduled sessions" />
        <KPICard label="Pending Evaluations" value={kpi.pendingEvaluations} caption="Awaiting review" />
        <KPICard label="Recommendations Made" value={kpi.recommendationsMade} caption="AI-generated insights" />
      </div>

      {/* Main content grid */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        {/* Hiring Funnel Chart */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Hiring Funnel</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Candidate progression through pipeline stages</p>
          <div className="mt-4 w-full" style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData} margin={{ top: 16, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 12, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(37, 99, 235, 0.04)" }} />
                <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} barSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Candidates Pipeline */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Recent Candidates</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Latest profiles entering the pipeline</p>
          <div className="mt-4 divide-y divide-[#E5E7EB]">
            {(pipelineCandidates ?? []).slice(0, 5).map((candidate) => {
              const name = candidate.candidate_name || `Candidate ${candidate.candidate_id.slice(0, 8)}`;
              const stage = candidate.status.replaceAll("_", " ");
              const score = candidate.overall_match_score == null
                ? null
                : Math.round(candidate.overall_match_score * 100);
              return (
              <div key={candidate.id} className="flex items-center gap-3 py-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#E5E7EB] text-[#6b7280] text-xs font-semibold">
                  {name.charAt(0)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-[#111827] truncate">{name}</p>
                  <p className="text-xs text-[#6b7280] truncate">{candidate.job_title}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {score != null && <span className="text-xs font-semibold text-[#111827]">{score}%</span>}
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${stageBadgeColor(stage)}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${stageDotColor(stage)}`} />
                    {stage}
                  </span>
                </div>
              </div>
              );
            })}
            {!pipelineCandidates?.length && (
              <p className="py-8 text-center text-sm text-slate-500">No candidates have entered the HR pipeline.</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Link href="/hr/candidates" className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-4 hover:bg-[#f9fafb]">
          <p className="text-sm font-medium text-[#111827]">View Candidates</p>
          <p className="text-xs text-[#6b7280] mt-0.5">Browse full pipeline</p>
        </Link>
        <Link href="/hr/interviews" className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-4 hover:bg-[#f9fafb]">
          <p className="text-sm font-medium text-[#111827]">Schedule Interview</p>
          <p className="text-xs text-[#6b7280] mt-0.5">Manage sessions</p>
        </Link>
        <Link href="/hr/reports" className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-4 hover:bg-[#f9fafb]">
          <p className="text-sm font-medium text-[#111827]">Generate Report</p>
          <p className="text-xs text-[#6b7280] mt-0.5">Export hiring analytics</p>
        </Link>
      </div>
    </DashboardShell>
  );
}
