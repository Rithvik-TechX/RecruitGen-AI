"use client";

import { useState, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useJobs, useInterviews, useRankings, useMarkSectionSeen } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError, validateMeetingLink } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { InterviewType, Job } from "@/types";

function typeBadge(type: string): string {
  const map: Record<string, string> = {
    phone: "bg-sky-50 text-sky-700",
    video: "bg-violet-50 text-violet-700",
    onsite: "bg-amber-50 text-amber-700",
    technical: "bg-blue-50 text-blue-700",
    hr: "bg-emerald-50 text-emerald-700",
    panel: "bg-rose-50 text-rose-700",
  };
  return map[type] ?? "bg-slate-100 text-slate-700";
}

function statusBadge(status: string): string {
  const map: Record<string, string> = {
    scheduled: "bg-blue-50 text-blue-700",
    confirmed: "bg-emerald-50 text-emerald-700",
    in_progress: "bg-amber-50 text-amber-700",
    completed: "bg-green-50 text-green-700",
    cancelled: "bg-red-50 text-red-700",
    no_show: "bg-slate-100 text-slate-700",
    rescheduled: "bg-indigo-50 text-indigo-700",
  };
  return map[status] ?? "bg-slate-100 text-slate-700";
}

interface ScheduleForm {
  scheduled_at: string;
  duration_minutes: number;
  interview_type: InterviewType;
  meeting_link: string;
  notes: string;
}

const defaultForm: ScheduleForm = {
  scheduled_at: "",
  duration_minutes: 30,
  interview_type: "video",
  meeting_link: "",
  notes: "",
};

export default function HRInterviewsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>("");
  const [form, setForm] = useState<ScheduleForm>(defaultForm);

  const { data: jobs, isLoading: jobsLoading } = useJobs();
  const { data: interviewsData, isLoading: interviewsLoading } = useInterviews(selectedJobId || undefined);
  const { data: rankingsData } = useRankings(selectedJobId || undefined);
  const queryClient = useQueryClient();
  const { toast, dismiss } = useToast();
  const markSeen = useMarkSectionSeen();
  useEffect(() => { markSeen.mutate("hr_interviews"); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedJob: Job | undefined = jobs?.find((j) => j.id === selectedJobId);
  const rankings = rankingsData?.rankings ?? [];

  // Build candidate name lookup from rankings
  const candidateNameMap = new Map(
    rankings.map((r) => [r.candidate_id, r.candidate_name || `Candidate ${r.candidate_id.slice(0, 8)}`])
  );

  const selectedCandidateName = candidateNameMap.get(selectedCandidateId) || "";

  const scheduleMutation = useMutation({
    mutationFn: (payload: {
      candidate_id: string;
      job_id: string;
      scheduled_at: string;
      duration_minutes: number;
      interview_type: InterviewType;
      meeting_link: string;
      notes: string;
    }) => api.post(`/jobs/${payload.job_id}/interviews`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews", selectedJobId] });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      setShowModal(false);
      setForm(defaultForm);
      setSelectedCandidateId("");
      toast.success("Interview scheduled successfully!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to schedule interview."));
    },
  });

  const interviews = interviewsData?.interviews ?? [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCandidateId) {
      toast.warning("Please select a candidate.");
      return;
    }
    if (!form.scheduled_at) {
      toast.warning("Please select a date and time.");
      return;
    }
    const linkError = validateMeetingLink(form.meeting_link);
    if (linkError) {
      toast.warning(linkError);
      return;
    }
    const toastId = toast.loading("Scheduling interview…");
    scheduleMutation.mutate(
      {
        candidate_id: selectedCandidateId,
        job_id: selectedJobId,
        ...form,
      },
      { onSettled: () => dismiss(toastId) },
    );
  };

  const openModal = () => {
    setForm(defaultForm);
    setSelectedCandidateId("");
    setShowModal(true);
  };

  return (
    <DashboardShell
      title="Interview Management"
      description="Schedule and manage interviews across all positions."
      actions={
        selectedJobId ? (
          <button
            onClick={openModal}
            className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
          >
            Schedule Interview
          </button>
        ) : null
      }
    >
      {/* Job Selector */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
        <label htmlFor="job-select-interview" className="block text-sm font-medium text-slate-700 mb-2">
          Select Job Position
        </label>
        <select
          id="job-select-interview"
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full max-w-md rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
        >
          <option value="">Choose a job…</option>
          {jobsLoading && <option disabled>Loading jobs…</option>}
          {jobs?.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title} — {job.department ?? job.location ?? "General"}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {!selectedJobId ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">Select a Job Position</h3>
          <p className="mt-2 text-sm text-slate-500">Choose a job from the dropdown to view and schedule interviews.</p>
        </div>
      ) : interviewsLoading ? (
        <div className="grid gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-4 w-48 rounded bg-slate-200" />
                  <div className="h-3 w-32 rounded bg-slate-100" />
                </div>
                <div className="h-6 w-20 rounded-full bg-slate-200" />
              </div>
            </div>
          ))}
        </div>
      ) : interviews.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No Interviews Scheduled</h3>
          <p className="mt-2 text-sm text-slate-500">Click &ldquo;Schedule Interview&rdquo; to set up the first session.</p>
        </div>
      ) : (
        /* ── Interview Table ─────────────────────────── */
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Candidate</th>
                  <th className="px-6 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Date & Time</th>
                  <th className="px-6 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Duration</th>
                  <th className="px-6 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3.5 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {interviews.map((interview) => {
                  const candName = candidateNameMap.get(interview.candidate_id) || `Candidate ${interview.candidate_id.slice(0, 8)}`;
                  return (
                    <tr key={interview.id} className="hover:bg-slate-50/50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-blue-600 text-xs font-semibold">
                            {candName[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-900">{candName}</p>
                            <p className="text-xs text-slate-500">{selectedJob?.title ?? ""}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${typeBadge(interview.interview_type)}`}>
                          {interview.interview_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                        {new Date(interview.scheduled_at).toLocaleDateString("en-US", {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}{" "}
                        at{" "}
                        {new Date(interview.scheduled_at).toLocaleTimeString("en-US", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {interview.duration_minutes} min
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusBadge(interview.status)}`}>
                          {interview.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {interview.meeting_link ? (
                          <a
                            href={interview.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-medium text-blue-600 hover:text-blue-700 transition"
                          >
                            Join →
                          </a>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Schedule Modal ────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Schedule Interview</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 transition">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Candidate Selector (dropdown, no UUID entry) */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Candidate</label>
                {rankings.length > 0 ? (
                  <select
                    required
                    value={selectedCandidateId}
                    onChange={(e) => setSelectedCandidateId(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  >
                    <option value="">Select a candidate…</option>
                    {rankings.map((r) => (
                      <option key={r.candidate_id} value={r.candidate_id}>
                        {r.candidate_name || `Candidate ${r.candidate_id.slice(0, 8)}`} — {Math.round(r.final_score * 100)}% match
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-sm text-slate-500 py-2">No ranked candidates. Run AI Matching first.</p>
                )}
              </div>

              {/* Read-only selected candidate info */}
              {selectedCandidateName && (
                <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-bold">
                      {selectedCandidateName[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{selectedCandidateName}</p>
                      <p className="text-xs text-slate-500">
                        {selectedJob?.title ?? ""} — {selectedJob?.department ?? selectedJob?.location ?? "General"}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Date & Time</label>
                  <input
                    type="datetime-local"
                    required
                    value={form.scheduled_at}
                    onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Duration</label>
                  <select
                    value={form.duration_minutes}
                    onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })}
                    className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  >
                    <option value={15}>15 minutes</option>
                    <option value={30}>30 minutes</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>60 minutes</option>
                    <option value={90}>90 minutes</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Interview Type</label>
                <select
                  value={form.interview_type}
                  onChange={(e) => setForm({ ...form, interview_type: e.target.value as InterviewType })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                >
                  <option value="phone">Phone</option>
                  <option value="video">Video</option>
                  <option value="onsite">Onsite</option>
                  <option value="technical">Technical</option>
                  <option value="hr">HR</option>
                  <option value="panel">Panel</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Meeting Link</label>
                <input
                  type="url"
                  value={form.meeting_link}
                  onChange={(e) => setForm({ ...form, meeting_link: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="https://meet.google.com/..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={3}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition resize-none"
                  placeholder="Any additional notes…"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scheduleMutation.isPending || !selectedCandidateId}
                  className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {scheduleMutation.isPending ? "Scheduling…" : "Schedule Interview"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
