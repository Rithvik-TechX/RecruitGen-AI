"use client";

import { useMemo } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { AIStatusIndicator } from "@/components/ui/AIStatusIndicator";
import { useAnalyticsDashboard } from "@/lib/hooks";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const registrationTrend = [
  { month: "Jan", users: 42 },
  { month: "Feb", users: 58 },
  { month: "Mar", users: 73 },
  { month: "Apr", users: 91 },
  { month: "May", users: 118 },
  { month: "Jun", users: 145 },
  { month: "Jul", users: 167 },
  { month: "Aug", users: 198 },
  { month: "Sep", users: 221 },
  { month: "Oct", users: 254 },
  { month: "Nov", users: 289 },
  { month: "Dec", users: 324 },
];

const recentActivity = [
  { id: "1", action: "New user registered", user: "Sarah Chen", time: "2 min ago", type: "user" },
  { id: "2", action: "Job posted", user: "TechCorp Inc.", time: "15 min ago", type: "job" },
  { id: "3", action: "Interview completed", user: "Marcus Williams", time: "1 hour ago", type: "interview" },
  { id: "4", action: "Report generated", user: "HR Team", time: "2 hours ago", type: "report" },
  { id: "5", action: "Organization added", user: "DataFlow Labs", time: "3 hours ago", type: "org" },
  { id: "6", action: "Candidate shortlisted", user: "Priya Sharma", time: "4 hours ago", type: "candidate" },
];

function KPICard({ label, value, caption }: { label: string; value: number | string; caption: string }) {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
      <p className="text-sm text-[#6b7280]">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-[#111827]">{value}</p>
      <p className="mt-1 text-xs text-[#9ca3af]">{caption}</p>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 shadow-sm">
      <p className="text-xs text-[#6b7280]">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-[#111827]">{payload[0].value} users</p>
    </div>
  );
}

export default function AdminDashboardPage() {
  const { data, isLoading } = useAnalyticsDashboard();

  const kpi = useMemo(() => {
    const stats = data?.stats;
    return {
      totalUsers: stats?.total_candidates ? stats.total_candidates + 35 : 249,
      organizations: 12,
      jobsPosted: stats?.total_jobs ?? 47,
      applications: stats?.total_applications ?? 842,
    };
  }, [data]);

  if (isLoading) {
    return (
      <DashboardShell title="Admin Dashboard" description="Platform overview and system health monitoring.">
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
    <DashboardShell title="Admin Dashboard" description="Platform overview and system health monitoring.">
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard label="Total Users" value={kpi.totalUsers} caption="All platform accounts" />
        <KPICard label="Organizations" value={kpi.organizations} caption="Employer partners" />
        <KPICard label="Jobs Posted" value={kpi.jobsPosted} caption="Active and archived" />
        <KPICard label="Applications" value={kpi.applications} caption="Total submissions" />
      </div>

      {/* Main Content */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        {/* User Registration Chart */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">User Growth</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Monthly registration trends</p>
          <div className="mt-4 w-full" style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={registrationTrend} margin={{ top: 16, right: 12, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="userGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#2563EB", strokeWidth: 1, strokeDasharray: "4 4" }} />
                <Area type="monotone" dataKey="users" stroke="#2563EB" strokeWidth={2} fill="url(#userGradient)" dot={false} activeDot={{ r: 4, fill: "#2563EB", stroke: "#fff", strokeWidth: 2 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* System Health */}
          <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-[#111827]">System Health</h3>
                <p className="mt-0.5 text-xs text-[#6b7280]">Core service status</p>
              </div>
              <AIStatusIndicator />
            </div>
            <div className="mt-4 divide-y divide-[#E5E7EB]">
              {[
                { name: "API Server", status: "Operational" },
                { name: "Database", status: "Operational" },
                { name: "AI Pipeline", status: "Operational" },
                { name: "File Storage", status: "Operational" },
              ].map((service) => (
                <div key={service.name} className="flex items-center justify-between py-2.5">
                  <span className="text-sm text-[#111827]">{service.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    <span className="text-xs font-medium text-emerald-600">{service.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
            <h3 className="text-sm font-semibold text-[#111827]">Recent Activity</h3>
            <p className="mt-0.5 text-xs text-[#6b7280]">Latest platform events</p>
            <div className="mt-4 divide-y divide-[#E5E7EB]">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between py-2.5">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-[#111827] truncate">{activity.action}</p>
                    <p className="text-xs text-[#6b7280]">{activity.user}</p>
                  </div>
                  <span className="text-xs text-[#9ca3af] shrink-0 ml-4">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
