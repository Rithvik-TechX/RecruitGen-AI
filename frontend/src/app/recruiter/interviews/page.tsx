"use client";

import { useState, useCallback } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs, useInterviews } from "@/lib/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Job, InterviewSchedule, InterviewType, InterviewStatus } from "@/types";

const INTERVIEW_TYPE_OPTIONS: Array<{ label: string; value: InterviewType }> = [
  { label: "Phone Screen", value: "phone" },
  { label: "Video Call", value: "video" },
  { label: "On-site", value: "onsite" },
  { label: "Technical", value: "technical" },
  { label: "HR Round", value: "hr" },
  { label: "Panel", value: "panel" },
];

function interviewStatusBadge(status: InterviewStatus) {
  const map: Record<InterviewStatus, string> = {
    scheduled: "bg-blue-50 text-blue-700",
    confirmed: "bg-emerald-50 text-emerald-700",
    in_progress: "bg-amber-50 text-amber-700",
    completed: "bg-slate-100 text-slate-600",
    cancelled: "bg-red-50 text-red-600",
    no_show: "bg-red-50 text-red-600",
    rescheduled: "bg-violet-50 text-violet-700",
  };
  return map[status] ?? "bg-slate-100 text-slate-600";
}

function interviewTypeIcon(type: InterviewType) {
  const icons: Record<InterviewType, string> = {
    phone: "M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z",
    video: "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z",
    onsite: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
    technical: "M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4",
    hr: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
    panel: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
  };
  return icons[type] ?? icons.video;
}

interface ScheduleForm {
  candidate_id: string;
  scheduled_at: string;
  duration_minutes: string;
  interview_type: InterviewType;
  meeting_link: string;
  notes: string;
}

const emptyForm: ScheduleForm = {
  candidate_id: "",
  scheduled_at: "",
  duration_minutes: "60",
  interview_type: "video",
  meeting_link: "",
  notes: "",
};

export default function RecruiterInterviewsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<ScheduleForm>(emptyForm);

  const jobsQuery = useJobs();
  const interviewsQuery = useInterviews(selectedJobId || undefined);
  const queryClient = useQueryClient();

  const jobs: Job[] = jobsQuery.data ?? [];
  const interviews: InterviewSchedule[] = interviewsQuery.data?.interviews ?? [];

  const scheduleMutation = useMutation({
    mutationFn: async (data: ScheduleForm) => {
      const payload = {
        candidate_id: data.candidate_id,
        scheduled_at: data.scheduled_at,
        duration_minutes: Number(data.duration_minutes),
        interview_type: data.interview_type,
        meeting_link: data.meeting_link || undefined,
        notes: data.notes || undefined,
      };
      const res = await api.post(`/jobs/${selectedJobId}/interviews`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews", selectedJobId] });
      setShowModal(false);
      setForm(emptyForm);
    },
  });

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    },
    [],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.candidate_id || !form.scheduled_at) return;
    scheduleMutation.mutate(form);
  };

  return (
    <DashboardShell
      title="Interview Scheduling"
      description="Manage upcoming candidate interviews and coordination."
      actions={
        <button
          onClick={() => setShowModal(true)}
          disabled={!selectedJobId}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Schedule Interview
        </button>
      }
    >
      {/* ── Job Selector ───────────────────────────── */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-5">
        <label className="block text-sm font-medium text-slate-700 mb-2">Select a Job Position</label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full max-w-md rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
        >
          <option value="">Choose a job to view interviews...</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>
              {j.title} — {j.department ?? "General"}
            </option>
          ))}
        </select>
      </div>

      {/* ── Interview Content ──────────────────────── */}
      {!selectedJobId ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">Select a job</h3>
          <p className="mt-2 text-sm text-slate-500">
            Choose a job position above to view scheduled interviews.
          </p>
        </div>
      ) : interviewsQuery.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
              <div className="h-5 w-3/4 rounded bg-slate-200" />
              <div className="mt-3 h-4 w-1/2 rounded bg-slate-100" />
              <div className="mt-4 h-3 w-full rounded bg-slate-100" />
              <div className="mt-2 h-3 w-2/3 rounded bg-slate-100" />
            </div>
          ))}
        </div>
      ) : interviews.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No interviews scheduled</h3>
          <p className="mt-2 text-sm text-slate-500">
            Click &quot;Schedule Interview&quot; to create the first one.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {interviews.map((interview) => (
            <div
              key={interview.id}
              className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 transition hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d={interviewTypeIcon(interview.interview_type)} />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {interview.candidate_id.slice(0, 12)}
                    </p>
                    <p className="text-xs text-slate-500 capitalize">
                      {interview.interview_type.replace("_", " ")} interview
                    </p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${interviewStatusBadge(interview.status)}`}
                >
                  {interview.status.replace("_", " ")}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Date & Time</p>
                  <p className="mt-1 text-sm font-medium text-slate-900">
                    {new Date(interview.scheduled_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(interview.scheduled_at).toLocaleTimeString("en-US", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Duration</p>
                  <p className="mt-1 text-sm font-medium text-slate-900">
                    {interview.duration_minutes} minutes
                  </p>
                </div>
              </div>

              {interview.meeting_link && (
                <div className="mt-3">
                  <a
                    href={interview.meeting_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Join Meeting
                  </a>
                </div>
              )}

              {interview.notes && (
                <p className="mt-3 text-xs text-slate-500 line-clamp-2">{interview.notes}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Schedule Interview Modal ───────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          />
          <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-lg bg-white p-8 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Schedule Interview</h2>
                <p className="mt-1 text-sm text-slate-500">
                  for {jobs.find((j) => j.id === selectedJobId)?.title ?? "this position"}
                </p>
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

            {scheduleMutation.isError && (
              <div className="mb-4 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                Failed to schedule interview. Please try again.
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Candidate ID *</label>
                <input
                  name="candidate_id"
                  value={form.candidate_id}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder="Enter candidate ID"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Date & Time *</label>
                  <input
                    name="scheduled_at"
                    type="datetime-local"
                    value={form.scheduled_at}
                    onChange={handleChange}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Duration (min)</label>
                  <input
                    name="duration_minutes"
                    type="number"
                    value={form.duration_minutes}
                    onChange={handleChange}
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    placeholder="60"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Interview Type</label>
                <select
                  name="interview_type"
                  value={form.interview_type}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                >
                  {INTERVIEW_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Meeting Link</label>
                <input
                  name="meeting_link"
                  value={form.meeting_link}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder="https://meet.google.com/..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                <textarea
                  name="notes"
                  value={form.notes}
                  onChange={handleChange}
                  rows={3}
                  className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 resize-none"
                  placeholder="Any additional notes for this interview..."
                />
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
                  disabled={scheduleMutation.isPending}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {scheduleMutation.isPending ? (
                    <>
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Scheduling…
                    </>
                  ) : (
                    "Schedule Interview"
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
