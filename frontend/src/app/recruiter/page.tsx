"use client";

import { useMemo } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs, useAnalyticsDashboard, useAnalyticsSkills } from "@/lib/hooks";
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
} from "recharts";
import type { Job } from "@/types";

const PIE_COLORS = ["#4f6ef7", "#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444"];

/* ── KPI Card ──────────────────────────────────────────── */

function KpiCard({
  label,
  value,
  caption,
}: {
  label: string;
  value: string | number;
  caption: string;
}) {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
      <p className="text-sm text-[#6b7280]">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-[#111827]">{value}</p>
      <p className="mt-1 text-xs text-[#9ca3af]">{caption}</p>
    </div>
  );
}

function SkeletonKpi() {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5 animate-pulse">
      <div className="space-y-3">
        <div className="h-3.5 w-24 rounded bg-[#f3f4f6]" />
        <div className="h-7 w-16 rounded bg-[#f3f4f6]" />
        <div className="h-3 w-32 rounded bg-[#f3f4f6]" />
      </div>
    </div>
  );
}

/* ── Custom Tooltip ────────────────────────────────────── */

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 shadow-sm">
      <p className="text-xs text-[#6b7280]">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-[#111827]">{payload[0].value}</p>
    </div>
  );
}

/* ── Page ──────────────────────────────────────────────── */

export default function RecruiterDashboardPage() {
  const jobsQuery = useJobs();
  const analyticsQuery = useAnalyticsDashboard();
  const skillsQuery = useAnalyticsSkills();

  const jobs: Job[] = jobsQuery.data ?? [];
  const stats = analyticsQuery.data?.stats;
  const pipeline = analyticsQuery.data?.pipeline;

  const kpis = useMemo(
    () => ({
      totalJobs: stats?.total_jobs ?? jobs.length,
      activeApps: stats?.total_applications ?? 0,
      shortlisted: stats?.shortlisted ?? 0,
      interviews: stats?.interviews_scheduled ?? 0,
      hiringRate: stats?.hiring_rate ?? 0,
    }),
    [stats, jobs.length],
  );

  const pipelineData = useMemo(() => {
    if (pipeline) {
      return [
        { stage: "Active Jobs", count: pipeline.active_jobs ?? 0 },
        { stage: "Pending Reviews", count: pipeline.pending_reviews ?? 0 },
        { stage: "Interviews", count: pipeline.interviews_this_week ?? 0 },
      ];
    }
    return [
      { stage: "Active Jobs", count: kpis.totalJobs },
      { stage: "Applications", count: kpis.activeApps },
      { stage: "Shortlisted", count: kpis.shortlisted },
      { stage: "Interviews", count: kpis.interviews },
    ];
  }, [pipeline, kpis]);

  const topSkills = skillsQuery.data ?? [];
  const recentJobs = jobs.slice(0, 5);
  const isLoading = analyticsQuery.isLoading;

  return (
    <DashboardShell
      title="Recruiter Dashboard"
      description="Coordinate roles, applications, and hiring velocity."
    >
      {/* ── KPI Cards ─────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <SkeletonKpi key={i} />)
        ) : (
          <>
            <KpiCard label="Total Jobs" value={kpis.totalJobs} caption="All job postings" />
            <KpiCard label="Applications" value={kpis.activeApps} caption="Profiles under review" />
            <KpiCard label="Shortlisted" value={kpis.shortlisted} caption="Qualified candidates" />
            <KpiCard label="Interviews" value={kpis.interviews} caption="Scheduled meetings" />
            <KpiCard label="Hiring Rate" value={`${kpis.hiringRate}%`} caption="Conversion to hire" />
          </>
        )}
      </div>

      {/* ── Pipeline + Skills ─────────────────────────── */}
      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        {/* Pipeline Bar Chart */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Hiring Pipeline</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Candidates across hiring stages</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 12, fill: "#6b7280" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(37, 99, 235, 0.04)" }} />
                <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} barSize={36} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Skills Pie */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Top Skills Distribution</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Most common skills in your talent pool</p>
          {topSkills.length === 0 ? (
            <div className="mt-8 flex flex-col items-center justify-center py-12 text-[#9ca3af]">
              <p className="text-sm font-medium">No skill data available yet</p>
              <p className="text-xs mt-1">Data will appear as candidates apply</p>
            </div>
          ) : (
            <div className="mt-4 flex items-center gap-6">
              <div className="h-56 w-56 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={topSkills.slice(0, 6)}
                      dataKey="count"
                      nameKey="skill_name"
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      innerRadius={50}
                      paddingAngle={3}
                      strokeWidth={0}
                    >
                      {topSkills.slice(0, 6).map((_, idx) => (
                        <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: "8px", border: "1px solid #E5E7EB", fontSize: "13px", boxShadow: "0 1px 2px rgba(0,0,0,0.05)" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2.5 flex-1">
                {topSkills.slice(0, 6).map((skill, idx) => (
                  <div key={skill.skill_name} className="flex items-center gap-2.5 text-sm">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }}
                    />
                    <span className="text-[#111827] truncate">{skill.skill_name}</span>
                    <span className="text-[#9ca3af] ml-auto shrink-0">({skill.count})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Recent Jobs + Quick Actions ───────────── */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        {/* Recent Jobs */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Recent Jobs</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Latest jobs added to your pipeline</p>
          {jobsQuery.isLoading ? (
            <div className="mt-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4 py-2">
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 w-3/4 rounded bg-[#f3f4f6]" />
                    <div className="h-3 w-1/2 rounded bg-[#f3f4f6]" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentJobs.length === 0 ? (
            <div className="mt-6 flex flex-col items-center justify-center py-12 text-[#9ca3af]">
              <p className="text-sm font-medium">No recent activity</p>
              <p className="text-xs mt-1">Jobs will appear here as you create them</p>
            </div>
          ) : (
            <div className="mt-3 divide-y divide-[#E5E7EB]">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-[#111827] truncate">{job.title}</p>
                    <p className="text-xs text-[#6b7280] mt-0.5">
                      {job.department ?? "General"} · {job.location ?? "Remote"}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
                      job.status === "active"
                        ? "bg-emerald-50 text-emerald-700"
                        : job.status === "draft"
                          ? "bg-gray-100 text-gray-600"
                          : job.status === "closed"
                            ? "bg-red-50 text-red-600"
                            : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${
                      job.status === "active" ? "bg-emerald-500" : job.status === "draft" ? "bg-gray-400" : job.status === "closed" ? "bg-red-500" : "bg-amber-500"
                    }`} />
                    {job.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Quick Actions</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Common tasks at a glance</p>
          <div className="mt-5 space-y-2">
            {[
              { label: "Post a New Job", href: "/recruiter/jobs" },
              { label: "Review Applications", href: "/recruiter/applications" },
              { label: "View Rankings", href: "/recruiter/rankings" },
              { label: "Schedule Interview", href: "/recruiter/interviews" },
              { label: "Generate Report", href: "/recruiter/reports" },
            ].map((action) => (
              <a
                key={action.label}
                href={action.href}
                className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-4 py-2.5 text-sm font-medium text-[#111827] hover:bg-[#f9fafb]"
              >
                {action.label}
                <svg className="h-4 w-4 text-[#9ca3af]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </a>
            ))}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
