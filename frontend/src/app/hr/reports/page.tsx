"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useReports } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import api from "@/lib/api";
import type {
  AnalyticsReportData,
  HiringReportData,
  MatchReportData,
  Report,
  ReportListItem,
  ReportStatus,
  ReportType,
} from "@/types";

const CHART_COLORS = ["#2563eb", "#0f766e", "#d97706", "#7c3aed", "#dc2626", "#0891b2"];

function statusConfig(status: ReportStatus) {
  const map = {
    pending: ["Pending", "bg-slate-400"],
    generating: ["Generating", "bg-amber-400"],
    completed: ["Completed", "bg-emerald-500"],
    failed: ["Failed", "bg-red-500"],
  } as const;
  return map[status];
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function DownloadIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
      <path strokeLinecap="round" d="M6 6l12 12M18 6 6 18" />
    </svg>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <p className="truncate text-xs font-medium uppercase text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{value}</p>
    </div>
  );
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="min-w-0">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-950 dark:text-white">{title}</h3>
        {description && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>}
      </div>
      {children}
    </section>
  );
}

function HiringReportView({ data }: { data: HiringReportData }) {
  const summary = data.summary;
  const metrics = [
    ["Total Jobs", summary.total_jobs],
    ["Applications", summary.total_applications],
    ["Screened", summary.screened],
    ["Shortlisted", summary.shortlisted],
    ["Interviewed", summary.interviewed],
    ["Selected", summary.selected],
    ["Rejected", summary.rejected],
  ];

  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map(([label, value]) => <MetricCard key={label} label={String(label)} value={value} />)}
      </div>

      <Section title="Executive Summary">
        <p className="rounded-lg border border-blue-100 bg-blue-50 p-5 text-sm leading-7 text-slate-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-slate-200">
          {data.executive_summary}
        </p>
      </Section>

      <div className="grid min-w-0 gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Section title="Pipeline Funnel" description="Candidate progression through the hiring cycle">
          <div className="h-72 min-w-0 rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.pipeline} layout="vertical" margin={{ top: 8, right: 16, left: 12, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis type="category" dataKey="stage" width={72} tick={{ fontSize: 11, fill: "#475569" }} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[0, 5, 5, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Section>

        <Section title="Recommendations" description="AI recommendation distribution">
          <div className="grid gap-3">
            {(["hire", "consider", "reject"] as const).map((decision, index) => (
              <div key={decision} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-4 dark:border-slate-700 dark:bg-slate-900">
                <div className="flex items-center gap-3">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CHART_COLORS[index + 1] }} />
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{humanize(decision)}</span>
                </div>
                <span className="text-xl font-semibold text-slate-950 dark:text-white">{data.recommendation_summary[decision]}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <Section title="Top Applicant Skills" description="Most frequently detected skills across applicant profiles">
        {data.top_skills.length ? (
          <div className="flex flex-wrap gap-2">
            {data.top_skills.map((skill) => (
              <span key={skill.skill_name} className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
                {skill.skill_name}
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{skill.count}</span>
              </span>
            ))}
          </div>
        ) : (
          <p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">No applicant skills are available for this period.</p>
        )}
      </Section>

      <Section title="Candidate Insights" description="Application, matching, and recommendation details">
        {data.candidates.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No candidates were included in this report.</p>
        ) : (
          <>
            <div className="hidden overflow-hidden rounded-lg border border-slate-200 md:block dark:border-slate-700">
              <table className="w-full table-fixed text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                  <tr>
                    <th className="w-[18%] px-4 py-3">Candidate</th>
                    <th className="w-[23%] px-4 py-3">Job Applied</th>
                    <th className="w-[12%] px-3 py-3">Match</th>
                    <th className="w-[12%] px-3 py-3">Skill</th>
                    <th className="w-[16%] px-3 py-3">Recommendation</th>
                    <th className="w-[19%] px-3 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-900">
                  {data.candidates.map((candidate, index) => (
                    <tr key={`${candidate.candidate_name}-${candidate.job_applied}-${index}`}>
                      <td className="break-words px-4 py-4 font-medium text-slate-900 dark:text-white">{candidate.candidate_name}</td>
                      <td className="break-words px-4 py-4 text-slate-600 dark:text-slate-300">{candidate.job_applied}</td>
                      <td className="px-3 py-4">{candidate.match_score != null ? `${candidate.match_score}%` : "Pending"}</td>
                      <td className="px-3 py-4">{candidate.skill_score != null ? `${candidate.skill_score}%` : "Pending"}</td>
                      <td className="px-3 py-4">{candidate.recommendation ? humanize(candidate.recommendation) : "Pending"}</td>
                      <td className="break-words px-3 py-4">{humanize(candidate.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="grid gap-3 md:hidden">
              {data.candidates.map((candidate, index) => (
                <div key={`${candidate.candidate_name}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
                  <p className="font-semibold text-slate-900 dark:text-white">{candidate.candidate_name}</p>
                  <p className="mt-1 text-sm text-slate-500">{candidate.job_applied}</p>
                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <div><span className="text-slate-500">Match</span><p className="font-medium">{candidate.match_score != null ? `${candidate.match_score}%` : "Pending"}</p></div>
                    <div><span className="text-slate-500">Skill</span><p className="font-medium">{candidate.skill_score != null ? `${candidate.skill_score}%` : "Pending"}</p></div>
                    <div><span className="text-slate-500">Recommendation</span><p className="font-medium">{candidate.recommendation ? humanize(candidate.recommendation) : "Pending"}</p></div>
                    <div><span className="text-slate-500">Status</span><p className="font-medium">{humanize(candidate.status)}</p></div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Section>
    </div>
  );
}

function ChartPanel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-w-0 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <h4 className="text-sm font-semibold text-slate-900 dark:text-white">{title}</h4>
      <div className="mt-4 h-64 min-w-0">{children}</div>
    </div>
  );
}

function AnalyticsReportView({ data }: { data: AnalyticsReportData }) {
  const metrics = [
    ["Applications", data.summary.applications],
    ["Conversion Rate", `${data.summary.conversion_rate}%`],
    ["Average Match", `${data.summary.average_match_score}%`],
    ["Average Skill", `${data.summary.average_skill_score}%`],
  ];
  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map(([label, value]) => <MetricCard key={label} label={String(label)} value={value} />)}
      </div>
      <Section title="Executive Summary">
        <p className="rounded-lg border border-blue-100 bg-blue-50 p-5 text-sm leading-7 text-slate-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-slate-200">
          {data.executive_summary}
        </p>
      </Section>
      <div className="grid min-w-0 gap-5 xl:grid-cols-2">
        <ChartPanel title="Application Trend">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.application_trend} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
              <Tooltip />
              <Area dataKey="value" type="monotone" stroke="#2563eb" fill="#dbeafe" strokeWidth={2} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Status Distribution">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data.status_distribution} dataKey="value" nameKey="label" innerRadius={48} outerRadius={82} paddingAngle={3} isAnimationActive={false}>
                {data.status_distribution.map((_, index) => <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Recommendation Distribution">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.recommendation_distribution} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" radius={[5, 5, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Match Score Distribution">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.match_score_distribution} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
              <Tooltip />
              <Bar dataKey="value" fill="#7c3aed" radius={[5, 5, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>
    </div>
  );
}

function MatchReportView({ data }: { data: MatchReportData }) {
  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Total Matches" value={data.summary.total_matches} />
        <MetricCard label="Average Overall" value={`${data.summary.average_overall_score}%`} />
      </div>
      <Section title="Executive Summary">
        <p className="rounded-lg border border-blue-100 bg-blue-50 p-5 text-sm leading-7 text-slate-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-slate-200">
          {data.executive_summary}
        </p>
      </Section>
      <Section title="Candidate Match Scores" description="AI score breakdown for matched applicants">
        {data.matches.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No match results are available for this report.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
            <table className="w-full table-fixed text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                <tr>
                  <th className="w-[30%] px-4 py-3">Candidate</th>
                  <th className="px-3 py-3">Overall</th>
                  <th className="px-3 py-3">Skill</th>
                  <th className="px-3 py-3">Experience</th>
                  <th className="px-3 py-3">Education</th>
                  <th className="px-3 py-3">Semantic</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-900">
                {data.matches.map((item, index) => (
                  <tr key={`${item.candidate}-${index}`}>
                    <td className="break-words px-4 py-4 font-medium text-slate-900 dark:text-white">{item.candidate}</td>
                    <td className="px-3 py-4">{item.overall_score}%</td>
                    <td className="px-3 py-4">{item.skill_score}%</td>
                    <td className="px-3 py-4">{item.experience_score}%</td>
                    <td className="px-3 py-4">{item.education_score}%</td>
                    <td className="px-3 py-4">{item.semantic_score}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

function ReportViewer({
  report,
  onClose,
}: {
  report: Report;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const [downloading, setDownloading] = useState<"pdf" | "excel" | "csv" | null>(null);

  const download = async (format: "pdf" | "excel" | "csv") => {
    setDownloading(format);
    try {
      const suffix = format === "pdf" ? "download" : format;
      const response = await api.get(`/reports/${report.id}/${suffix}`, { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = url;
      const ext = format === "excel" ? "xlsx" : format;
      anchor.download = `${report.title.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.${ext}`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success(`${format.toUpperCase()} report downloaded.`);
    } catch (error) {
      toast.error(getApiError(error, `Failed to download ${format.toUpperCase()} report.`));
    } finally {
      setDownloading(null);
    }
  };

  const header = report.data.header;
  return (
    <div className="fixed inset-0 z-50 bg-slate-950/55 p-0 backdrop-blur-sm sm:p-4">
      <div className="mx-auto flex h-full w-full max-w-7xl flex-col overflow-hidden bg-slate-50 shadow-2xl sm:h-[94vh] sm:rounded-lg dark:bg-slate-950">
        <header className="shrink-0 border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900 sm:px-6">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase text-blue-600">RecruitGen AI Report</p>
              <h2 className="mt-1 break-words text-xl font-semibold text-slate-950 dark:text-white">{report.title}</h2>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
                <span>{header.organization_name}</span>
                <span>Generated {formatDate(header.generated_date)}</span>
                <span>{header.report_period}</span>
              </div>
            </div>
            <button type="button" onClick={onClose} aria-label="Close report" title="Close report" className="shrink-0 rounded-md p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800">
              <CloseIcon />
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={() => download("pdf")} disabled={downloading !== null} className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              <DownloadIcon /> {downloading === "pdf" ? "Preparing PDF..." : "Download PDF"}
            </button>
            <button type="button" onClick={() => download("excel")} disabled={downloading !== null} className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
              <DownloadIcon /> {downloading === "excel" ? "Preparing Excel..." : "Download Excel"}
            </button>
            <button type="button" onClick={() => download("csv")} disabled={downloading !== null} className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
              <DownloadIcon /> {downloading === "csv" ? "Preparing CSV..." : "Download CSV"}
            </button>
          </div>
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6">
          {report.data.kind === "hiring" && <HiringReportView data={report.data} />}
          {report.data.kind === "analytics" && <AnalyticsReportView data={report.data} />}
          {report.data.kind === "match" && <MatchReportView data={report.data} />}
          {report.data.kind === "generic" && (
            <p className="rounded-lg border border-slate-200 bg-white p-6 text-sm leading-7 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
              {report.data.executive_summary}
            </p>
          )}
        </main>
      </div>
    </div>
  );
}

export default function HRReportsPage() {
  const { data: reports, isLoading } = useReports();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const detailQuery = useQuery<Report>({
    queryKey: ["reports", "detail", selectedId],
    queryFn: async () => (await api.get<Report>(`/reports/${selectedId}`)).data,
    enabled: Boolean(selectedId),
  });

  const generateMutation = useMutation({
    mutationFn: (type: ReportType) =>
      api.post<Report>("/reports/", {
        report_type: type,
        title: type === "hiring" ? "Hiring Performance Report" : "Recruitment Analytics Report",
      }),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      queryClient.setQueryData(["reports", "detail", data.id], data);
      setSelectedId(data.id);
      toast.success("Report generated successfully.");
    },
    onError: (error) => toast.error(getApiError(error, "Failed to generate report.")),
  });

  return (
    <DashboardShell
      title="HR Reports"
      description="Create presentation-ready hiring and recruitment analytics reports."
      actions={
        <div className="flex flex-wrap gap-2">
          <button onClick={() => generateMutation.mutate("hiring")} disabled={generateMutation.isPending} className="rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            Generate Hiring Report
          </button>
          <button onClick={() => generateMutation.mutate("analytics")} disabled={generateMutation.isPending} className="rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
            Generate Analytics Report
          </button>
        </div>
      }
    >
      {isLoading ? (
        <div className="grid gap-4">
          {Array.from({ length: 3 }).map((_, index) => <div key={index} className="h-32 animate-pulse rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900" />)}
        </div>
      ) : reports?.length ? (
        <div className="grid gap-4">
          {reports.map((report: ReportListItem) => {
            const [statusLabel, dot] = statusConfig(report.status);
            return (
              <button key={report.id} type="button" onClick={() => setSelectedId(report.id)} className="w-full rounded-lg border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-blue-300 hover:shadow-md dark:border-slate-700 dark:bg-slate-900">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="break-words text-base font-semibold text-slate-950 dark:text-white">{report.title}</h3>
                      <span className="rounded bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 dark:bg-blue-950 dark:text-blue-200">{humanize(report.report_type)}</span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{report.summary}</p>
                    <p className="mt-3 text-xs text-slate-400">{report.organization_name} · {report.report_period} · {formatDate(report.created_at)}</p>
                  </div>
                  <span className="inline-flex shrink-0 items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
                    <span className={`h-2 w-2 rounded-full ${dot}`} /> {statusLabel}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center dark:border-slate-700 dark:bg-slate-900">
          <h3 className="text-lg font-semibold text-slate-950 dark:text-white">No reports generated</h3>
          <p className="mt-2 text-sm text-slate-500">Generate a hiring or analytics report to begin.</p>
        </div>
      )}

      {selectedId && detailQuery.isLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 backdrop-blur-sm">
          <div className="rounded-lg bg-white px-6 py-5 text-sm font-medium text-slate-700 shadow-xl">Preparing report...</div>
        </div>
      )}
      {selectedId && detailQuery.isError && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-lg bg-white p-6 text-center shadow-xl">
            <h3 className="font-semibold text-slate-950">Report could not be loaded</h3>
            <p className="mt-2 text-sm text-slate-500">{getApiError(detailQuery.error, "Please try again.")}</p>
            <button onClick={() => setSelectedId(null)} className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white">Close</button>
          </div>
        </div>
      )}
      {selectedId && detailQuery.data && <ReportViewer report={detailQuery.data} onClose={() => setSelectedId(null)} />}
    </DashboardShell>
  );
}
