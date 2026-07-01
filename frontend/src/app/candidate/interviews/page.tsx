"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { useMyInterviews } from "@/lib/hooks";
import type { InterviewSchedule } from "@/types";

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

function statusBadge(status: string): { cls: string; label: string } {
  const map: Record<string, { cls: string; label: string }> = {
    scheduled: { cls: "bg-blue-50 text-blue-700 border-blue-200", label: "Scheduled" },
    confirmed: { cls: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Confirmed" },
    in_progress: { cls: "bg-amber-50 text-amber-700 border-amber-200", label: "In Progress" },
    completed: { cls: "bg-green-50 text-green-700 border-green-200", label: "Completed" },
    cancelled: { cls: "bg-red-50 text-red-600 border-red-200", label: "Cancelled" },
    no_show: { cls: "bg-slate-100 text-slate-600 border-slate-200", label: "No Show" },
    rescheduled: { cls: "bg-indigo-50 text-indigo-700 border-indigo-200", label: "Rescheduled" },
  };
  return map[status] ?? { cls: "bg-slate-100 text-slate-600 border-slate-200", label: status };
}

function isUpcoming(scheduledAt: string): boolean {
  return new Date(scheduledAt) > new Date();
}

export default function CandidateInterviewsPage() {
  const { data: interviews, isLoading } = useMyInterviews();

  const sortedInterviews = [...(interviews ?? [])].sort(
    (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
  );

  const upcoming = sortedInterviews.filter((i) => isUpcoming(i.scheduled_at) && i.status !== "cancelled");
  const past = sortedInterviews.filter((i) => !isUpcoming(i.scheduled_at) || i.status === "cancelled");

  return (
    <DashboardShell title="My Interviews" description="View your scheduled and past interviews.">
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-5 w-48 rounded bg-slate-200" />
                  <div className="h-3 w-32 rounded bg-slate-100" />
                </div>
                <div className="h-6 w-20 rounded-full bg-slate-200" />
              </div>
            </div>
          ))}
        </div>
      ) : sortedInterviews.length === 0 ? (
        <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-16 text-center">
          <svg className="mx-auto h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-slate-900">No Interviews Yet</h3>
          <p className="mt-2 text-sm text-slate-500">
            Your scheduled interviews will appear here once the hiring team schedules them.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Upcoming Interviews */}
          {upcoming.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                Upcoming Interviews ({upcoming.length})
              </h3>
              <div className="space-y-4">
                {upcoming.map((interview) => (
                  <InterviewCard key={interview.id} interview={interview} highlight />
                ))}
              </div>
            </div>
          )}

          {/* Past Interviews */}
          {past.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-slate-500 mb-4">
                Past Interviews ({past.length})
              </h3>
              <div className="space-y-4">
                {past.map((interview) => (
                  <InterviewCard key={interview.id} interview={interview} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </DashboardShell>
  );
}

function InterviewCard({ interview, highlight }: { interview: InterviewSchedule; highlight?: boolean }) {
  const badge = statusBadge(interview.status);
  const date = new Date(interview.scheduled_at);

  return (
    <div
      className={`rounded-xl border bg-white shadow-sm p-5 transition hover:shadow-md ${
        highlight ? "border-blue-200 ring-1 ring-blue-100" : "border-slate-200/90"
      }`}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          {/* Date badge */}
          <div className="flex flex-col items-center justify-center rounded-xl bg-blue-50 px-3 py-2 text-center shrink-0">
            <span className="text-xs font-medium text-blue-600 uppercase">
              {date.toLocaleDateString("en-US", { month: "short" })}
            </span>
            <span className="text-xl font-bold text-blue-800 leading-tight">
              {date.getDate()}
            </span>
            <span className="text-xs text-blue-500">
              {date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${typeBadge(interview.interview_type)}`}>
                {interview.interview_type} Interview
              </span>
              <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${badge.cls}`}>
                {badge.label}
              </span>
            </div>
            <p className="text-sm text-slate-600">
              {date.toLocaleDateString("en-US", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })}{" "}
              — {interview.duration_minutes} minutes
            </p>
            {interview.notes && (
              <p className="text-sm text-slate-500 mt-1">
                <span className="font-medium text-slate-600">Notes:</span> {interview.notes}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2 items-end shrink-0">
          {interview.meeting_link && interview.status !== "cancelled" && (
            <a
              href={interview.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
              Join Meeting
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
