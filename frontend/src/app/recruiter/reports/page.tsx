"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { useReports } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ReportListItem, ReportType, ReportStatus } from "@/types";

function reportStatusBadge(status: ReportStatus) {
  const map: Record<ReportStatus, string> = {
    pending: "bg-slate-100 text-slate-600",
    generating: "bg-blue-50 text-blue-700",
    completed: "bg-emerald-50 text-emerald-700",
    failed: "bg-red-50 text-red-600",
  };
  return map[status] ?? "bg-slate-100 text-slate-600";
}

function reportTypeBadge(type: ReportType) {
  const map: Record<ReportType, string> = {
    candidate: "bg-violet-50 text-violet-700",
    hiring: "bg-blue-50 text-blue-700",
    match: "bg-amber-50 text-amber-700",
    interview: "bg-emerald-50 text-emerald-700",
    analytics: "bg-rose-50 text-rose-600",
  };
  return map[type] ?? "bg-slate-100 text-slate-600";
}

function reportTypeIcon(type: ReportType) {
  const icons: Record<ReportType, string> = {
    candidate: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
    hiring: "M21 13.255A23.193 23.193 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
    match: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
    interview: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
    analytics: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  };
  return icons[type] ?? icons.analytics;
}

const GENERATE_BUTTONS: Array<{ label: string; type: ReportType; icon: string }> = [
  {
    label: "Hiring Report",
    type: "hiring",
    icon: "M21 13.255A23.193 23.193 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  },
  {
    label: "Analytics Report",
    type: "analytics",
    icon: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  },
];

export default function RecruiterReportsPage() {
  const reportsQuery = useReports();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const reports: ReportListItem[] = reportsQuery.data ?? [];

  const generateMutation = useMutation({
    mutationFn: async (reportType: ReportType) => {
      const res = await api.post("/reports/", {
        report_type: reportType,
        title: reportType === "hiring" ? "Hiring Performance Report" : "Recruitment Analytics Report",
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast.success("Report generated successfully!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to generate report."));
    },
  });

  return (
    <DashboardShell
      title="Reports"
      description="Generate and view hiring reports and analytics summaries."
    >
      {/* ── Generate Buttons ──────────────────────── */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
        <h3 className="text-base font-semibold text-slate-900">Generate New Report</h3>
        <p className="mt-1 text-sm text-slate-500">
          Create AI-powered reports for your recruitment pipeline
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          {GENERATE_BUTTONS.map((btn) => (
            <button
              key={btn.type}
              onClick={() => generateMutation.mutate(btn.type)}
              disabled={generateMutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:border-slate-300 disabled:opacity-50"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d={btn.icon} />
              </svg>
              {btn.label}
            </button>
          ))}
        </div>

        {generateMutation.isError && (
          <div className="mt-3 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            Failed to generate report. Please try again.
          </div>
        )}

        {generateMutation.isSuccess && (
          <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-700">
            Report generation started successfully!
          </div>
        )}
      </div>

      {/* ── Reports List ──────────────────────────── */}
      {reportsQuery.isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-slate-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 w-1/3 rounded bg-slate-200" />
                  <div className="h-3 w-1/2 rounded bg-slate-100" />
                </div>
                <div className="h-6 w-20 rounded-full bg-slate-200" />
              </div>
            </div>
          ))}
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No reports yet</h3>
          <p className="mt-2 text-sm text-slate-500">
            Generate your first report using the buttons above.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 transition hover:shadow-md"
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-500">
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={reportTypeIcon(report.report_type)} />
                  </svg>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h3 className="text-base font-semibold text-slate-900">{report.title}</h3>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${reportTypeBadge(report.report_type)}`}
                    >
                      {report.report_type}
                    </span>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${reportStatusBadge(report.status)}`}
                    >
                      {report.status === "generating" && (
                        <svg className="mr-1 h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                      )}
                      {report.status}
                    </span>
                  </div>

                  {report.summary && (
                    <p className="mt-2 text-sm text-slate-600 line-clamp-2">{report.summary}</p>
                  )}

                  <div className="mt-3 flex items-center gap-4">
                    <span className="text-xs text-slate-400">
                      {new Date(report.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>

                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardShell>
  );
}
