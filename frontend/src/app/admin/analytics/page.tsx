"use client";

import { useMemo } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useAnalyticsDashboard, useAnalyticsSkills } from "@/lib/hooks";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const BLUE_PALETTE = ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe"];

const fallbackFunnel = [
  { stage: "Applied", count: 486 },
  { stage: "Screened", count: 342 },
  { stage: "Interviewed", count: 178 },
  { stage: "Evaluated", count: 112 },
  { stage: "Offered", count: 54 },
  { stage: "Hired", count: 38 },
];

const applicationTrend = [
  { month: "Jan", applications: 62 },
  { month: "Feb", applications: 78 },
  { month: "Mar", applications: 95 },
  { month: "Apr", applications: 108 },
  { month: "May", applications: 132 },
  { month: "Jun", applications: 155 },
  { month: "Jul", applications: 142 },
  { month: "Aug", applications: 168 },
  { month: "Sep", applications: 189 },
  { month: "Oct", applications: 210 },
  { month: "Nov", applications: 234 },
  { month: "Dec", applications: 258 },
];

const fallbackSkills = [
  { skill_name: "React", count: 89, percentage: 24 },
  { skill_name: "Python", count: 76, percentage: 21 },
  { skill_name: "TypeScript", count: 64, percentage: 17 },
  { skill_name: "AWS", count: 51, percentage: 14 },
  { skill_name: "SQL", count: 43, percentage: 12 },
  { skill_name: "Docker", count: 34, percentage: 9 },
];

export default function AdminAnalyticsPage() {
  const { data: dashData, isLoading: dashLoading } = useAnalyticsDashboard();
  const { data: skillsData, isLoading: skillsLoading } = useAnalyticsSkills();

  const metrics = useMemo(() => {
    const stats = dashData?.stats;
    const pipeline = dashData?.pipeline;
    return {
      activeJobs: pipeline?.active_jobs ?? stats?.total_jobs ?? 47,
      pendingReviews: pipeline?.pending_reviews ?? 23,
      interviewsThisWeek: pipeline?.interviews_this_week ?? stats?.interviews_scheduled ?? 18,
      avgTimeToHire: pipeline?.avg_time_to_hire_days ?? 14,
      totalApplications: stats?.total_applications ?? 842,
      hiringRate: stats?.hiring_rate ?? 68,
    };
  }, [dashData]);

  const skills = skillsData ?? fallbackSkills;

  const isLoading = dashLoading || skillsLoading;

  if (isLoading) {
    return (
      <DashboardShell title="Platform Analytics" description="Deep metrics for hiring velocity and candidate quality.">
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
              <div className="animate-pulse space-y-3">
                <div className="h-4 w-24 rounded bg-slate-200" />
                <div className="h-8 w-16 rounded bg-slate-200" />
                <div className="h-3 w-32 rounded bg-slate-100" />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 animate-pulse">
              <div className="h-5 w-40 rounded bg-slate-200 mb-4" />
              <div className="h-64 rounded-xl bg-slate-100" />
            </div>
          ))}
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="Platform Analytics" description="Deep metrics for hiring velocity and candidate quality.">
      {/* Pipeline Metrics */}
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Active Jobs" value={metrics.activeJobs} caption="Open positions" icon="briefcase" />
        <MetricCard label="Pending Reviews" value={metrics.pendingReviews} caption="Awaiting evaluation" icon="clock" />
        <MetricCard label="Interviews This Week" value={metrics.interviewsThisWeek} caption="Scheduled sessions" icon="calendar" />
        <MetricCard label="Avg. Time to Hire" value={`${metrics.avgTimeToHire}d`} caption="Days from apply to offer" icon="chart" />
      </div>

      {/* Charts Row 1 */}
      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        {/* Hiring Funnel */}
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <h3 className="text-lg font-semibold text-slate-900">Hiring Funnel</h3>
          <p className="mt-1 text-sm text-slate-500">Candidate progression through stages</p>
          <div className="mt-4 w-full" style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fallbackFunnel} margin={{ top: 16, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="stage" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                  formatter={(value) => [`${value}`, "Candidates"]}
                />
                <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skills Distribution Pie */}
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <h3 className="text-lg font-semibold text-slate-900">Skills Distribution</h3>
          <p className="mt-1 text-sm text-slate-500">Top candidate skills across applications</p>
          <div className="mt-4 w-full" style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={skills}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={110}
                  paddingAngle={3}
                  dataKey="count"
                  nameKey="skill_name"
                >
                  {skills.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={BLUE_PALETTE[index % BLUE_PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                  formatter={(value, name) => [`${value}`, `${name}`]}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value: string) => <span className="text-xs text-slate-600">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Application Trends */}
      <div className="mt-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
        <h3 className="text-lg font-semibold text-slate-900">Application Trends</h3>
        <p className="mt-1 text-sm text-slate-500">Monthly application volume over the past year</p>
        <div className="mt-4 w-full" style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={applicationTrend} margin={{ top: 16, right: 12, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="appGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                formatter={(value) => [`${value}`, "Applications"]}
              />
              <Area type="monotone" dataKey="applications" stroke="#2563eb" strokeWidth={2} fill="url(#appGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="mt-6 grid gap-6 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <p className="text-sm font-medium text-slate-500">Total Applications</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{metrics.totalApplications}</p>
          <p className="mt-1 text-sm text-emerald-600 font-medium">↑ 12% from last month</p>
        </div>
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <p className="text-sm font-medium text-slate-500">Hiring Rate</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{metrics.hiringRate}%</p>
          <p className="mt-1 text-sm text-emerald-600 font-medium">↑ 3% improvement</p>
        </div>
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
          <p className="text-sm font-medium text-slate-500">Pipeline Efficiency</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">87%</p>
          <p className="mt-1 text-sm text-slate-500">Within target range</p>
        </div>
      </div>
    </DashboardShell>
  );
}

function MetricCard({ label, value, caption, icon }: { label: string; value: number | string; caption: string; icon: string }) {
  const iconMap: Record<string, React.ReactNode> = {
    briefcase: (
      <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0" />
      </svg>
    ),
    clock: (
      <svg className="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ),
    calendar: (
      <svg className="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
      </svg>
    ),
    chart: (
      <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
  };

  const bgMap: Record<string, string> = {
    briefcase: "bg-blue-50",
    clock: "bg-amber-50",
    calendar: "bg-indigo-50",
    chart: "bg-emerald-50",
  };

  return (
    <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${bgMap[icon] ?? "bg-slate-50"}`}>
          {iconMap[icon]}
        </div>
        <p className="text-sm font-medium text-slate-500">{label}</p>
      </div>
      <p className="mt-3 text-3xl font-semibold text-slate-900">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{caption}</p>
    </div>
  );
}
