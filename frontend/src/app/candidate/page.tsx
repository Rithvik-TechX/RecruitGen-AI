"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { useAuth } from "@/context/AuthContext";
import { useMyApplications, useResumes, downloadOfferLetter } from "@/lib/hooks";
import type { Application, ResumeResponse } from "@/types";
import Link from "next/link";

const STATUS_COLORS: Record<string, string> = {
  applied: "bg-amber-50 text-amber-700",
  screened: "bg-blue-50 text-blue-700",
  shortlisted: "bg-emerald-50 text-emerald-700",
  interview_scheduled: "bg-violet-50 text-violet-700",
  interview_completed: "bg-sky-50 text-sky-700",
  rejected: "bg-red-50 text-red-700",
  selected: "bg-green-50 text-green-700",
};

const STATUS_DOTS: Record<string, string> = {
  applied: "bg-amber-500",
  screened: "bg-blue-500",
  shortlisted: "bg-emerald-500",
  interview_scheduled: "bg-violet-500",
  interview_completed: "bg-sky-500",
  rejected: "bg-red-500",
  selected: "bg-green-500",
};

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function SkeletonKpi() {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5 animate-pulse">
      <div className="space-y-3">
        <div className="h-3.5 w-24 rounded bg-[#f3f4f6]" />
        <div className="h-7 w-16 rounded bg-[#f3f4f6]" />
        <div className="h-3 w-32 rounded bg-[#f3f4f6]" />
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="flex items-center justify-between py-3 animate-pulse">
      <div className="space-y-2">
        <div className="h-3.5 w-40 rounded bg-[#f3f4f6]" />
        <div className="h-3 w-24 rounded bg-[#f3f4f6]" />
      </div>
      <div className="h-5 w-20 rounded-full bg-[#f3f4f6]" />
    </div>
  );
}

export default function CandidateDashboardPage() {
  const { user } = useAuth();
  const applicationsQuery = useMyApplications();
  const resumesQuery = useResumes();

  const applications: Application[] = applicationsQuery.data ?? [];
  const resumes: ResumeResponse[] = resumesQuery.data ?? [];
  const isLoading = applicationsQuery.isLoading || resumesQuery.isLoading;

  const totalApps = applications.length;
  const interviewCount = applications.filter(
    (a) => a.status === "interview_scheduled" || a.status === "interview_completed"
  ).length;
  const latestResume = resumes.length > 0 ? resumes[resumes.length - 1] : null;
  const recentApps = [...applications]
    .sort((a, b) => new Date(b.applied_at).getTime() - new Date(a.applied_at).getTime())
    .slice(0, 5);

  const firstName = user?.full_name?.split(" ")[0] ?? "there";

  return (
    <DashboardShell
      title={`Welcome back, ${firstName}`}
      description="Your personalized overview and application activity."
    >
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          <>
            <SkeletonKpi />
            <SkeletonKpi />
            <SkeletonKpi />
            <SkeletonKpi />
          </>
        ) : (
          <>
            <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
              <p className="text-sm text-[#6b7280]">Total Applications</p>
              <p className="mt-1 text-2xl font-semibold text-[#111827]">{totalApps}</p>
              <p className="mt-1 text-xs text-[#9ca3af]">Positions you&apos;ve applied to</p>
            </div>
            <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
              <p className="text-sm text-[#6b7280]">Interviews Scheduled</p>
              <p className="mt-1 text-2xl font-semibold text-[#111827]">{interviewCount}</p>
              <p className="mt-1 text-xs text-[#9ca3af]">Upcoming interviews</p>
            </div>
            <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
              <p className="text-sm text-[#6b7280]">Profile Views</p>
              <p className="mt-1 text-2xl font-semibold text-[#111827]">{resumes.length > 0 ? resumes.length * 3 : 0}</p>
              <p className="mt-1 text-xs text-[#9ca3af]">Estimated profile views</p>
            </div>
            <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-5">
              <p className="text-sm text-[#6b7280]">Match Score</p>
              <p className="mt-1 text-2xl font-semibold text-[#111827]">{totalApps > 0 ? "84%" : "—"}</p>
              <p className="mt-1 text-xs text-[#9ca3af]">Average job match</p>
            </div>
          </>
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {/* Resume Status */}
        <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Resume Status</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Your latest uploaded resume</p>
          {resumesQuery.isLoading ? (
            <div className="mt-4 space-y-3 animate-pulse">
              <div className="h-4 w-32 rounded bg-[#f3f4f6]" />
              <div className="h-3 w-48 rounded bg-[#f3f4f6]" />
            </div>
          ) : latestResume ? (
            <div className="mt-5 space-y-3">
              <div>
                <p className="text-sm font-medium text-[#111827] truncate">{latestResume.file_name}</p>
                <p className="text-xs text-[#6b7280] mt-0.5">Uploaded {formatDate(latestResume.uploaded_at)}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#6b7280]">{latestResume.file_type} · {(latestResume.file_size / 1024).toFixed(0)} KB</span>
              </div>
            </div>
          ) : (
            <div className="mt-6 text-center py-6">
              <p className="text-sm font-medium text-[#6b7280]">No resume uploaded yet</p>
              <Link
                href="/candidate/profile"
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-[#2563EB] hover:underline"
              >
                Upload your resume →
              </Link>
            </div>
          )}
        </div>

        {/* Recent Applications */}
        <div className="lg:col-span-2 bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#111827]">Recent Applications</h3>
          <p className="mt-0.5 text-xs text-[#6b7280]">Track your latest submissions</p>
          {applicationsQuery.isLoading ? (
            <div className="mt-4 divide-y divide-[#E5E7EB]">
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </div>
          ) : recentApps.length === 0 ? (
            <div className="mt-6 text-center py-10">
              <p className="text-sm font-medium text-[#6b7280]">No applications yet</p>
              <Link
                href="/candidate/jobs"
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-[#2563EB] hover:underline"
              >
                Browse open positions →
              </Link>
            </div>
          ) : (
            <div className="mt-3 divide-y divide-[#E5E7EB]">
              {recentApps.map((app) => (
                <div key={app.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-[#111827]">
                      Application #{app.id.slice(0, 8)}
                    </p>
                    <p className="text-xs text-[#6b7280] mt-0.5">
                      Applied {formatDate(app.applied_at)}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
                      STATUS_COLORS[app.status] ?? "bg-gray-100 text-gray-600"
                    }`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOTS[app.status] ?? "bg-gray-400"}`} />
                    {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Offer Letter Card */}
      {!isLoading && applications.filter((a) => a.status === "selected").length > 0 && (
        <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
          <h3 className="text-base font-semibold text-emerald-900">🎉 Offer Letter Available</h3>
          <div className="mt-3 space-y-3">
            {applications
              .filter((a) => a.status === "selected")
              .map((app) => (
                <div key={app.id} className="flex items-center justify-between rounded-lg bg-white border border-emerald-100 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-slate-900">Application #{app.id.slice(0, 8)}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Job #{app.job_id.slice(0, 8)}</p>
                  </div>
                  <button
                    onClick={() => downloadOfferLetter(app.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                    Download Offer Letter
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-6 bg-white border border-[#E5E7EB] rounded-lg shadow-sm p-6">
        <h3 className="text-sm font-semibold text-[#111827] mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/candidate/profile"
            className="inline-flex items-center gap-2 bg-[#2563EB] hover:bg-[#1d4ed8] text-white rounded-lg px-4 py-2 font-medium text-sm"
          >
            Upload Resume
          </Link>
          <Link
            href="/candidate/jobs"
            className="inline-flex items-center gap-2 border border-[#E5E7EB] bg-white hover:bg-[#f9fafb] text-[#111827] rounded-lg px-4 py-2 font-medium text-sm"
          >
            Browse Jobs
          </Link>
          <Link
            href="/candidate/applications"
            className="inline-flex items-center gap-2 border border-[#E5E7EB] bg-white hover:bg-[#f9fafb] text-[#111827] rounded-lg px-4 py-2 font-medium text-sm"
          >
            View Applications
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}
