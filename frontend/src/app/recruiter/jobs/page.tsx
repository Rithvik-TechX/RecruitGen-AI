"use client";

import { useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Job, JobStatus } from "@/types";

const STATUS_TABS: Array<{ label: string; value: JobStatus | "all" }> = [
  { label: "All", value: "all" },
  { label: "Active", value: "active" },
  { label: "Draft", value: "draft" },
  { label: "Closed", value: "closed" },
];

const JOB_TYPE_OPTIONS: Array<{ label: string; value: string }> = [
  { label: "Full Time", value: "full_time" },
  { label: "Part Time", value: "part_time" },
  { label: "Contract", value: "contract" },
  { label: "Internship", value: "internship" },
];

function statusBadge(status: JobStatus) {
  const map: Record<JobStatus, string> = {
    active: "bg-emerald-50 text-emerald-700",
    draft: "bg-slate-100 text-slate-600",
    paused: "bg-amber-50 text-amber-700",
    closed: "bg-red-50 text-red-600",
    archived: "bg-slate-100 text-slate-500",
  };
  return map[status] ?? "bg-slate-100 text-slate-600";
}

function apiErrorMessage(error: unknown, fallback: string): string {
  const maybeError = error as { response?: { data?: { detail?: string }; status?: number } };
  const detail = maybeError.response?.data?.detail;
  if (detail) return detail;
  if (maybeError.response?.status === 429) return "Quota exceeded. Please try again later.";
  if (maybeError.response?.status === 503) return "AI service unavailable. Please try again later.";
  return fallback;
}

interface CreateJobForm {
  title: string;
  department: string;
  description: string;
  location: string;
  salary_min: string;
  salary_max: string;
  employment_type: string;
  requirements: string;
  status: "active" | "draft";
}

const emptyForm: CreateJobForm = {
  title: "",
  department: "",
  description: "",
  location: "",
  salary_min: "",
  salary_max: "",
  employment_type: "full_time",
  requirements: "",
  status: "active",
};

export default function RecruiterJobsPage() {
  const [activeTab, setActiveTab] = useState<JobStatus | "all">("all");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<CreateJobForm>(emptyForm);
  // Track per-job analysis state: jobId → "loading" | "success" | "error"
  const [analyzeState, setAnalyzeState] = useState<Record<string, "loading" | "success" | "error">>({});
  const [analyzeErrors, setAnalyzeErrors] = useState<Record<string, string>>({});

  const statusFilter = activeTab === "all" ? undefined : activeTab;
  const jobsQuery = useJobs(statusFilter);
  const jobs: Job[] = jobsQuery.data ?? [];

  const queryClient = useQueryClient();
  const { toast, dismiss } = useToast();

  const createMutation = useMutation({
    mutationFn: async (data: CreateJobForm) => {
      const payload = {
        title: data.title,
        description: data.description,
        department: data.department || undefined,
        location: data.location || undefined,
        salary_min: data.salary_min ? Number(data.salary_min) : undefined,
        salary_max: data.salary_max ? Number(data.salary_max) : undefined,
        employment_type: data.employment_type || undefined,
        status: data.status,
      };
      const res = await api.post("/jobs/", payload);
      return res.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setShowModal(false);
      setForm(emptyForm);
      const statusLabel = variables.status === "active" ? "posted as Active" : "saved as Draft";
      toast.success(`Job "${variables.title}" ${statusLabel} successfully!`);
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to create job."));
    },
  });

  const handleAnalyze = useCallback(
    async (jobId: string) => {
      setAnalyzeState((prev) => ({ ...prev, [jobId]: "loading" }));
      setAnalyzeErrors((prev) => {
        const next = { ...prev };
        delete next[jobId];
        return next;
      });
      const toastId = toast.loading("Analyzing job description...");
      try {
        await api.post(`/jobs/${jobId}/analyze`);
        setAnalyzeState((prev) => ({ ...prev, [jobId]: "success" }));
        queryClient.invalidateQueries({ queryKey: ["jobs"] });
        dismiss(toastId);
        toast.success("Job analysis completed successfully!");
        setTimeout(() => {
          setAnalyzeState((prev) => {
            const next = { ...prev };
            delete next[jobId];
            return next;
          });
        }, 5000);
      } catch (err) {
        setAnalyzeState((prev) => ({ ...prev, [jobId]: "error" }));
        const msg = getApiError(err, "Failed to analyze job.");
        setAnalyzeErrors((prev) => ({ ...prev, [jobId]: msg }));
        dismiss(toastId);
        toast.error(msg);
      }
    },
    [queryClient, toast],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    },
    [],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.description) return;
    createMutation.mutate(form);
  };

  return (
    <DashboardShell
      title="Job Management"
      description="Create, manage, and track all hiring requisitions."
      actions={
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Create New Job
        </button>
      }
    >
      {/* ── Status Filter Tabs ─────────────────────── */}
      <div className="mb-6 flex gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              activeTab === tab.value
                ? "bg-blue-600 text-white shadow-sm"
                : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Job Grid ───────────────────────────────── */}
      {jobsQuery.isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
              <div className="h-5 w-3/4 rounded bg-slate-200" />
              <div className="mt-3 h-4 w-1/2 rounded bg-slate-100" />
              <div className="mt-4 h-3 w-full rounded bg-slate-100" />
              <div className="mt-2 h-3 w-2/3 rounded bg-slate-100" />
              <div className="mt-5 flex gap-2">
                <div className="h-8 w-20 rounded-lg bg-slate-200" />
                <div className="h-8 w-20 rounded-lg bg-slate-100" />
              </div>
            </div>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No jobs found</h3>
          <p className="mt-2 text-sm text-slate-500">Create your first job posting to get started.</p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
          >
            Create New Job
          </button>
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job) => {
            const jobAnalyzeState = analyzeState[job.id];
            const jobAnalyzeError = analyzeErrors[job.id];
            return (
              <div
                key={job.id}
                className="flex flex-col rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 transition hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <h3 className="text-base font-semibold text-slate-900 truncate">{job.title}</h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {job.department ?? "General"} · {job.location ?? "Remote"}
                    </p>
                  </div>
                  <span className={`ml-3 shrink-0 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadge(job.status)}`}>
                    {job.status}
                  </span>
                </div>

                <p className="mt-3 text-sm text-slate-600 line-clamp-2">{job.description}</p>

                <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
                  {job.salary_min != null && job.salary_max != null && (
                    <span>
                      ${job.salary_min.toLocaleString()} – ${job.salary_max.toLocaleString()}
                    </span>
                  )}
                  <span className="capitalize">{(job.employment_type ?? "full_time").replace("_", " ")}</span>
                </div>

                <div className="mt-auto pt-4 text-xs text-slate-400">
                  Created {new Date(job.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                </div>

                {/* Analysis feedback per card */}
                {jobAnalyzeState === "success" && (
                  <div className="mt-2 rounded-md bg-emerald-50 border border-emerald-200 px-3 py-1.5 text-xs text-emerald-700 flex items-center gap-1.5">
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Analysis completed successfully
                  </div>
                )}
                {jobAnalyzeState === "error" && (
                  <div className="mt-2 rounded-md bg-red-50 border border-red-200 px-3 py-1.5 text-xs text-red-700">
                    {jobAnalyzeError || "Analysis failed. Try again."}
                  </div>
                )}

                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => handleAnalyze(job.id)}
                    disabled={jobAnalyzeState === "loading"}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                  >
                    {jobAnalyzeState === "loading" ? (
                      <>
                        <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Analyzing…
                      </>
                    ) : (
                      <>
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        Analyze Job
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Create Job Modal ───────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          />
          <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-lg bg-white p-8 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Create New Job</h2>
                <p className="mt-1 text-sm text-slate-500">Fill in the details for the new position</p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {createMutation.isError && (
              <div className="mb-4 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {apiErrorMessage(createMutation.error, "Failed to create job. Please try again.")}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Job Title *</label>
                <input
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder="e.g. Senior Frontend Engineer"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
                  <input
                    name="department"
                    value={form.department}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    placeholder="e.g. Engineering"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
                  <input
                    name="location"
                    value={form.location}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    placeholder="e.g. San Francisco, CA"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description *</label>
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  required
                  rows={4}
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 resize-none"
                  placeholder="Describe the role, responsibilities, and ideal candidate..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Requirements</label>
                <textarea
                  name="requirements"
                  value={form.requirements}
                  onChange={handleChange}
                  rows={3}
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 resize-none"
                  placeholder="List key requirements, one per line..."
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Min Salary</label>
                  <input
                    name="salary_min"
                    type="number"
                    value={form.salary_min}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    placeholder="50000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Max Salary</label>
                  <input
                    name="salary_max"
                    type="number"
                    value={form.salary_max}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    placeholder="120000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Job Type</label>
                  <select
                    name="employment_type"
                    value={form.employment_type}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  >
                    {JOB_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* ── Post Status Selection ─────────────────── */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Post Status</label>
                <div className="flex gap-4">
                  <label
                    className={`flex-1 flex items-center gap-3 cursor-pointer rounded-lg border-2 p-3 transition ${
                      form.status === "active"
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="status"
                      value="active"
                      checked={form.status === "active"}
                      onChange={handleChange}
                      className="accent-blue-600"
                    />
                    <div>
                      <p className="text-sm font-medium text-slate-900">Post as Active</p>
                      <p className="text-xs text-slate-500">Job will be visible to candidates immediately</p>
                    </div>
                  </label>
                  <label
                    className={`flex-1 flex items-center gap-3 cursor-pointer rounded-lg border-2 p-3 transition ${
                      form.status === "draft"
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="status"
                      value="draft"
                      checked={form.status === "draft"}
                      onChange={handleChange}
                      className="accent-blue-600"
                    />
                    <div>
                      <p className="text-sm font-medium text-slate-900">Save as Draft</p>
                      <p className="text-xs text-slate-500">Review and publish later</p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className={`inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium text-white transition disabled:opacity-50 ${
                    form.status === "active"
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-blue-600 hover:bg-blue-700"
                  }`}
                >
                  {createMutation.isPending ? (
                    <>
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Creating…
                    </>
                  ) : form.status === "active" ? (
                    "Post Job"
                  ) : (
                    "Save as Draft"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
