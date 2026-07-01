"use client";

import { useMemo } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useAnalyticsDashboard, useAnalyticsSkills } from "@/lib/hooks";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import type { PieLabelRenderProps } from "recharts";

const PIE_COLORS = ["#2563eb", "#0ea5e9", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#ec4899", "#14b8a6"];

function KpiCard({
  label,
  value,
  icon,
  color,
  subtitle,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <div className={`rounded-xl p-2.5 ${color}`}>{icon}</div>
      </div>
      <p className="mt-3 text-3xl font-semibold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 rounded bg-slate-200" />
        <div className="h-10 w-10 rounded-xl bg-slate-200" />
      </div>
      <div className="mt-3 h-8 w-16 rounded bg-slate-200" />
      <div className="mt-2 h-3 w-32 rounded bg-slate-100" />
    </div>
  );
}

export default function RecruiterAnalyticsPage() {
  const dashboardQuery = useAnalyticsDashboard();
  const skillsQuery = useAnalyticsSkills();

  const stats = dashboardQuery.data?.stats;
  const pipeline = dashboardQuery.data?.pipeline;
  const topSkills = dashboardQuery.data?.top_skills ?? [];
  const skillsData = skillsQuery.data ?? [];

  const displaySkills = skillsData.length > 0 ? skillsData : topSkills;

  const kpis = useMemo(
    () => ({
      totalJobs: stats?.total_jobs ?? 0,
      totalApps: stats?.total_applications ?? 0,
      shortlisted: stats?.shortlisted ?? 0,
      interviews: stats?.interviews_scheduled ?? 0,
      hiringRate: stats?.hiring_rate ?? 0,
      totalCandidates: stats?.total_candidates ?? 0,
      rejected: stats?.rejected ?? 0,
    }),
    [stats],
  );

  const funnelData = useMemo(
    () => [
      { stage: "Applications", count: kpis.totalApps, fill: "#2563eb" },
      { stage: "Shortlisted", count: kpis.shortlisted, fill: "#8b5cf6" },
      { stage: "Interviews", count: kpis.interviews, fill: "#f59e0b" },
      { stage: "Rejected", count: kpis.rejected, fill: "#ef4444" },
    ],
    [kpis],
  );

  const pipelineMetrics = useMemo(
    () => [
      { label: "Active Jobs", value: pipeline?.active_jobs ?? kpis.totalJobs },
      { label: "Pending Reviews", value: pipeline?.pending_reviews ?? 0 },
      { label: "Interviews This Week", value: pipeline?.interviews_this_week ?? 0 },
      {
        label: "Avg Time to Hire",
        value: pipeline?.avg_time_to_hire_days != null ? `${pipeline.avg_time_to_hire_days}d` : "—",
      },
    ],
    [pipeline, kpis.totalJobs],
  );

  const isLoading = dashboardQuery.isLoading;

  return (
    <DashboardShell
      title="Analytics"
      description="Understand hiring performance and candidate flow metrics."
    >
      {/* ── KPI Summary ───────────────────────────── */}
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <KpiCard
              label="Total Jobs"
              value={kpis.totalJobs}
              color="bg-blue-50 text-blue-600"
              subtitle="All positions"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              }
            />
            <KpiCard
              label="Total Candidates"
              value={kpis.totalCandidates}
              color="bg-emerald-50 text-emerald-600"
              subtitle="Unique applicants"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              }
            />
            <KpiCard
              label="Interviews"
              value={kpis.interviews}
              color="bg-amber-50 text-amber-600"
              subtitle="Scheduled meetings"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              }
            />
            <KpiCard
              label="Hiring Rate"
              value={`${kpis.hiringRate}%`}
              color="bg-violet-50 text-violet-600"
              subtitle="Interview to hire conversion"
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              }
            />
          </>
        )}
      </div>

      {/* ── Charts ────────────────────────────────── */}
      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        {/* Hiring Funnel */}
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <h3 className="text-base font-semibold text-slate-900">Hiring Funnel</h3>
          <p className="mt-1 text-sm text-slate-500">Candidate progression through stages</p>
          {isLoading ? (
            <div className="mt-4 h-64 animate-pulse rounded-xl bg-slate-100" />
          ) : (
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="stage" tick={{ fontSize: 12, fill: "#64748b" }} />
                  <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: "12px",
                      border: "1px solid #e2e8f0",
                      fontSize: "13px",
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]} barSize={48}>
                    {funnelData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Top Skills Distribution */}
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <h3 className="text-base font-semibold text-slate-900">Top Skills Distribution</h3>
          <p className="mt-1 text-sm text-slate-500">Most common skills across candidates</p>
          {isLoading ? (
            <div className="mt-4 h-64 animate-pulse rounded-xl bg-slate-100" />
          ) : displaySkills.length === 0 ? (
            <div className="mt-8 flex flex-col items-center justify-center py-12 text-slate-400">
              <svg className="h-10 w-10 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
              <p className="text-sm">No skill data available</p>
            </div>
          ) : (
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={displaySkills.slice(0, 8)}
                    dataKey="count"
                    nameKey="skill_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    innerRadius={55}
                    paddingAngle={3}
                    label={(props: PieLabelRenderProps) =>
                      `${props.name ?? ""} (${Math.round((props.percent ?? 0) * 100)}%)`
                    }
                    labelLine={false}
                  >
                    {displaySkills.slice(0, 8).map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: "12px",
                      border: "1px solid #e2e8f0",
                      fontSize: "13px",
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: "12px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* ── Pipeline Metrics ──────────────────────── */}
      <div className="mt-6">
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <h3 className="text-base font-semibold text-slate-900">Pipeline Metrics</h3>
          <p className="mt-1 text-sm text-slate-500">Operational KPIs for your hiring pipeline</p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {isLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="animate-pulse rounded-xl bg-slate-50 p-5">
                    <div className="h-3 w-20 rounded bg-slate-200" />
                    <div className="mt-3 h-7 w-12 rounded bg-slate-200" />
                  </div>
                ))
              : pipelineMetrics.map((metric) => (
                  <div key={metric.label} className="rounded-xl bg-slate-50 p-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      {metric.label}
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">{metric.value}</p>
                  </div>
                ))}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
