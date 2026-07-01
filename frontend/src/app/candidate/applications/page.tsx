"use client";

import { useState, useMemo, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useMyApplications, downloadOfferLetter, useMarkSectionSeen } from "@/lib/hooks";
import type { Application, ApplicationStatus } from "@/types";

const STATUS_CONFIG: Record<
  string,
  { label: string; cls: string }
> = {
  applied: { label: "Applied", cls: "bg-amber-50 text-amber-700 border border-amber-200" },
  screened: { label: "Screened", cls: "bg-blue-50 text-blue-700 border border-blue-200" },
  shortlisted: { label: "Shortlisted", cls: "bg-indigo-50 text-indigo-700 border border-indigo-200" },
  interview_scheduled: { label: "Interview Scheduled", cls: "bg-violet-50 text-violet-700 border border-violet-200" },
  interview_completed: { label: "Interview Completed", cls: "bg-sky-50 text-sky-700 border border-sky-200" },
  selected: { label: "Selected", cls: "bg-emerald-50 text-emerald-700 border border-emerald-200" },
  rejected: { label: "Rejected", cls: "bg-red-50 text-red-700 border border-red-200" },
};

type FilterTab = "all" | ApplicationStatus;

const TABS: { key: FilterTab; label: string }[] = [
  { key: "all", label: "All" },
  { key: "applied", label: "Applied" },
  { key: "screened", label: "Screened" },
  { key: "shortlisted", label: "Shortlisted" },
  { key: "interview_scheduled", label: "Interview" },
  { key: "selected", label: "Selected" },
  { key: "rejected", label: "Rejected" },
];

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-6 py-4"><div className="h-4 w-32 rounded bg-slate-200" /></td>
      <td className="px-6 py-4"><div className="h-4 w-20 rounded bg-slate-200" /></td>
      <td className="px-6 py-4"><div className="h-6 w-24 rounded-full bg-slate-200" /></td>
      <td className="px-6 py-4"><div className="h-4 w-24 rounded bg-slate-100" /></td>
    </tr>
  );
}

export default function CandidateApplicationsPage() {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const applicationsQuery = useMyApplications();
  const markSeen = useMarkSectionSeen();
  useEffect(() => { markSeen.mutate("candidate_applications"); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const applications: Application[] = useMemo(() => applicationsQuery.data ?? [], [applicationsQuery.data]);

  const filtered = useMemo(() => {
    if (activeTab === "all") return applications;
    return applications.filter((a) => a.status === activeTab);
  }, [applications, activeTab]);

  const counts = useMemo(() => {
    const map: Record<string, number> = { all: applications.length };
    for (const a of applications) {
      map[a.status] = (map[a.status] ?? 0) + 1;
    }
    return map;
  }, [applications]);

  return (
    <DashboardShell title="My Applications" description="Track your active applications and their status.">
      {/* Filter Tabs */}
      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          const count = counts[tab.key] ?? 0;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-sm font-medium transition ${
                isActive
                  ? "bg-blue-600 text-white shadow-sm"
                  : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {tab.label}
              <span
                className={`inline-flex items-center justify-center min-w-[20px] h-5 rounded-full text-xs font-medium px-1.5 ${
                  isActive ? "bg-white/20 text-white" : "bg-slate-100 text-slate-500"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-slate-200/90 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Application ID
                </th>
                <th className="px-6 py-3.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Job ID
                </th>
                <th className="px-6 py-3.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Applied Date
                </th>
                <th className="px-6 py-3.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {applicationsQuery.isLoading ? (
                <>
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                </>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-16 text-center">
                    <svg
                      className="mx-auto h-10 w-10 text-slate-300"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"
                      />
                    </svg>
                    <p className="mt-3 text-base font-medium text-slate-700">
                      {activeTab === "all" ? "No applications yet" : `No ${TABS.find((t) => t.key === activeTab)?.label.toLowerCase()} applications`}
                    </p>
                    <p className="mt-1 text-sm text-slate-500">
                      {activeTab === "all"
                        ? "Start by browsing open positions and applying."
                        : "Try selecting a different filter."}
                    </p>
                  </td>
                </tr>
              ) : (
                filtered.map((app) => {
                  const cfg = STATUS_CONFIG[app.status] ?? {
                    label: app.status,
                    cls: "bg-slate-50 text-slate-600 border border-slate-200",
                  };
                  return (
                    <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-900">
                        #{app.id.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        #{app.job_id.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.cls}`}
                        >
                          {cfg.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">
                        {formatDate(app.applied_at)}
                      </td>
                      <td className="px-6 py-4">
                        {app.status === "selected" && (
                          <button
                            onClick={() => downloadOfferLetter(app.id)}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700"
                          >
                            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                            </svg>
                            Download Offer Letter
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      {!applicationsQuery.isLoading && applications.length > 0 && (
        <p className="mt-4 text-xs text-slate-400 text-right">
          Showing {filtered.length} of {applications.length} applications
        </p>
      )}
    </DashboardShell>
  );
}
