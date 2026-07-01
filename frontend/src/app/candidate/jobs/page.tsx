"use client";

import { useState, useMemo, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs, useResumes, useMarkSectionSeen } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Job, ResumeResponse } from "@/types";

const TYPE_LABELS: Record<string, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  internship: "Internship",
};

const TYPE_COLORS: Record<string, string> = {
  full_time: "bg-blue-50 text-blue-700 border border-blue-200",
  part_time: "bg-purple-50 text-purple-700 border border-purple-200",
  contract: "bg-amber-50 text-amber-700 border border-amber-200",
  internship: "bg-emerald-50 text-emerald-700 border border-emerald-200",
};

function formatSalary(min?: number, max?: number): string {
  if (!min && !max) return "Not specified";
  const fmt = (n: number) =>
    n >= 1000 ? `$${(n / 1000).toFixed(0)}k` : `$${n}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function SkeletonCard() {
  return (
    <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 animate-pulse">
      <div className="h-5 w-48 rounded bg-slate-200" />
      <div className="mt-2 h-4 w-32 rounded bg-slate-100" />
      <div className="mt-4 flex gap-2">
        <div className="h-6 w-20 rounded-full bg-slate-200" />
        <div className="h-6 w-24 rounded-full bg-slate-100" />
      </div>
      <div className="mt-4 h-4 w-36 rounded bg-slate-100" />
      <div className="mt-4 h-9 w-20 rounded-xl bg-slate-200" />
    </div>
  );
}

export default function CandidateJobsPage() {
  const [search, setSearch] = useState("");
  const [applyingJob, setApplyingJob] = useState<Job | null>(null);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [coverLetter, setCoverLetter] = useState("");

  const queryClient = useQueryClient();
  const markSeen = useMarkSectionSeen();
  useEffect(() => { markSeen.mutate("candidate_jobs"); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const { toast } = useToast();
  const jobsQuery = useJobs("active");
  const resumesQuery = useResumes();
  const jobs: Job[] = useMemo(() => jobsQuery.data ?? [], [jobsQuery.data]);
  const resumes: ResumeResponse[] = useMemo(() => resumesQuery.data ?? [], [resumesQuery.data]);

  const filtered = useMemo(() => {
    if (!search.trim()) return jobs;
    const q = search.toLowerCase();
    return jobs.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.department?.toLowerCase().includes(q) ||
        j.location?.toLowerCase().includes(q)
    );
  }, [jobs, search]);

  const applyMutation = useMutation({
    mutationFn: async (payload: { job_id: string }) => {
      const res = await api.post("/applications/", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["applications", "me"] });
      toast.success("Application submitted successfully!");
      setApplyingJob(null);
      setSelectedResumeId("");
      setCoverLetter("");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to submit application."));
    },
  });

  const openApplyModal = (job: Job) => {
    setApplyingJob(job);
    setSelectedResumeId(resumes.length > 0 ? resumes[0].id : "");
    setCoverLetter("");
  };

  const submitApplication = () => {
    if (!applyingJob) return;
    applyMutation.mutate({
      job_id: applyingJob.id,
    });
  };

  return (
    <DashboardShell title="Job Search" description="Explore open roles and find your next opportunity.">
      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Search by title, department, or location…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
          />
        </div>
      </div>

      {/* Job Grid */}
      {jobsQuery.isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
          <p className="mt-4 text-base font-medium text-slate-700">
            {search ? "No jobs match your search" : "No open positions right now"}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {search ? "Try adjusting your search terms." : "Check back soon for new opportunities."}
          </p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((job) => (
            <div
              key={job.id}
              className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition"
            >
              <div>
                <h3 className="text-base font-semibold text-slate-900 line-clamp-2">{job.title}</h3>
                <p className="mt-1 text-sm text-slate-500">
                  {job.department ?? "General"}
                  {job.location ? ` · ${job.location}` : ""}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      TYPE_COLORS[job.employment_type ?? ""] ?? "bg-slate-50 text-slate-600 border border-slate-200"
                    }`}
                  >
                    {TYPE_LABELS[job.employment_type ?? ""] ?? (job.employment_type || "Full-time").replace(/_/g, " ")}
                  </span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200">
                    {formatSalary(job.salary_min, job.salary_max)}
                  </span>
                </div>
                <p className="mt-3 text-xs text-slate-400">Posted {formatDate(job.created_at)}</p>
              </div>
              <button
                onClick={() => openApplyModal(job)}
                className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2.5 font-medium transition text-sm"
              >
                Apply
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Apply Modal */}
      {applyingJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setApplyingJob(null)}
          />
          <div className="relative z-10 w-full max-w-lg mx-4 rounded-lg bg-white shadow-xl p-6">
            <div className="flex items-start justify-between mb-5">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Apply for Position</h3>
                <p className="text-sm text-slate-500 mt-1">{applyingJob.title}</p>
              </div>
              <button
                onClick={() => setApplyingJob(null)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Select Resume <span className="text-red-500">*</span>
                </label>
                {resumes.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No resumes uploaded.{" "}
                    <a href="/candidate/profile" className="text-blue-600 hover:underline">
                      Upload one first
                    </a>
                    .
                  </p>
                ) : (
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white py-2.5 px-3 text-sm text-slate-900 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  >
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.file_name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Cover Letter <span className="text-slate-400">(optional)</span>
                </label>
                <textarea
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  rows={4}
                  placeholder="Why are you a great fit for this role?"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 px-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 resize-none"
                />
              </div>

              {applyMutation.isError && (
                <p className="text-sm text-red-600">Failed to submit application. Please try again.</p>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setApplyingJob(null)}
                className="border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-lg px-4 py-2.5 font-medium transition text-sm"
              >
                Cancel
              </button>
              <button
                onClick={submitApplication}
                disabled={!selectedResumeId || applyMutation.isPending}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2.5 font-medium transition text-sm disabled:opacity-50"
              >
                {applyMutation.isPending ? "Submitting…" : "Submit Application"}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
