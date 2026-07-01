"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { AIStatusIndicator } from "@/components/ui/AIStatusIndicator";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useResumes } from "@/lib/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  CandidateProfile,
  ResumeResponse,
  ResumeUploadResponse,
} from "@/types";

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

function ProficiencyBadge({ level }: { level?: string }) {
  const colors: Record<string, string> = {
    expert: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    advanced: "bg-blue-50 text-blue-700 border border-blue-200",
    intermediate: "bg-amber-50 text-amber-700 border border-amber-200",
    beginner: "bg-slate-50 text-slate-600 border border-slate-200",
  };
  const label = level ?? "—";
  const cls = colors[label.toLowerCase()] ?? "bg-slate-50 text-slate-600 border border-slate-200";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {label.charAt(0).toUpperCase() + label.slice(1)}
    </span>
  );
}

function SectionSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-3">
          <div className="h-4 w-1/3 rounded bg-slate-200" />
          <div className="h-4 w-1/2 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}

function apiErrorMessage(error: unknown, fallback: string): string {
  const maybeError = error as { response?: { data?: { detail?: string }; status?: number } };
  const detail = maybeError.response?.data?.detail;
  if (detail) return detail;
  if (maybeError.response?.status === 429) return "Quota exceeded. Please try again later.";
  if (maybeError.response?.status === 503) return "AI service unavailable. Please try again later.";
  return fallback;
}

export default function CandidateProfilePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedResumeId, setSelectedResumeId] = useState<string>("");
  const [parseStep, setParseStep] = useState(0);

  const resumesQuery = useResumes();
  const resumes: ResumeResponse[] = resumesQuery.data ?? [];
  const activeResumeId = selectedResumeId || resumes[0]?.id || "";

  const profileQuery = useQuery<CandidateProfile | null>({
    queryKey: ["candidate", "profile", "resume", activeResumeId],
    queryFn: async () => {
      const res = await api.get<CandidateProfile | null>(`/candidates/by-resume/${activeResumeId}`);
      return res.data;
    },
    enabled: !!user?.id && !!activeResumeId,
    staleTime: 0,
    gcTime: 0,
  });
  const profile = profileQuery.data;

  const uploadMutation = useMutation<ResumeUploadResponse, Error, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post<ResumeUploadResponse>("/resumes/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
    onSuccess: (resume) => {
      setSelectedResumeId(resume.id);
      queryClient.invalidateQueries({ queryKey: ["resumes", "me"] });
      queryClient.removeQueries({ queryKey: ["candidate", "profile"] });
      toast.success("Resume uploaded successfully!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to upload resume."));
    },
  });

  const parseMutation = useMutation<unknown, unknown, string>({
    mutationFn: async (resumeId: string) => {
      const res = await api.post(`/resumes/parse/${resumeId}`, null, {
        timeout: 120000,
      });
      return res.data;
    },
    onMutate: (resumeId) => {
      setSelectedResumeId(resumeId);
      setParseStep(0);
      queryClient.removeQueries({ queryKey: ["candidate", "profile"] });
    },
    onSuccess: async (_data, resumeId) => {
      await queryClient.invalidateQueries({ queryKey: ["resumes", "me"] });
      await queryClient.refetchQueries({
        queryKey: ["candidate", "profile", "resume", resumeId],
        exact: true,
      });
      toast.success("Resume parsed and profile generated!");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to parse resume."));
    },
    onSettled: () => {
      setParseStep(0);
    },
  });

  useEffect(() => {
    if (!parseMutation.isPending) return;
    let step = 0;
    const interval = setInterval(() => {
      step = Math.min(step + 1, 4);
      setParseStep(step);
    }, 3000);
    return () => clearInterval(interval);
  }, [parseMutation.isPending]);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      uploadMutation.mutate(files[0]);
    },
    [uploadMutation]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?";

  return (
    <DashboardShell title="Profile" description="Manage your candidate profile and resume.">
      {/* Profile Header */}
      <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 mb-6">
        <div className="flex items-center gap-5">
          <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-blue-600 text-xl font-semibold text-white shrink-0">
            {initials}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold text-slate-900">{user?.full_name ?? "—"}</h2>
              {profile?.parser_source && (
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                  profile.parser_source === "ai"
                    ? "bg-blue-50 text-blue-700"
                    : "bg-amber-50 text-amber-700"
                }`}>
                  {profile.parser_source === "ai" ? "AI Parsed Profile" : "Fallback Parsed Profile"}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500">{user?.email ?? "—"}</p>
            {profile?.phone && (
              <p className="text-sm text-slate-500 mt-0.5">{profile.phone}</p>
            )}
            <div className="flex gap-3 mt-2">
              {profile?.linkedin_url && (
                <a
                  href={profile.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline"
                >
                  LinkedIn
                </a>
              )}
              {profile?.github_url && (
                <a
                  href={profile.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline"
                >
                  GitHub
                </a>
              )}
            </div>
          </div>
        </div>
        {profile?.summary && (
          <p className="mt-4 text-sm text-slate-600 leading-relaxed">{profile.summary}</p>
        )}
        {profile && (() => {
          const stats = [
            ["Skills", profile.skills.length],
            ["Projects", profile.projects.length],
            ["Certifications", profile.certifications.length],
            ["Achievements", profile.achievements.length],
            ["Research", profile.research_experience.length],
            ["Links", profile.links.length],
          ].filter(([, v]) => (v as number) > 0);
          if (stats.length === 0) return null;
          return (
            <div className={`mt-5 grid grid-cols-2 gap-3 border-t border-slate-100 pt-5 sm:grid-cols-3 lg:grid-cols-${Math.min(stats.length, 6)}`}>
              {stats.map(([label, value]) => (
                <div key={label as string} className="rounded-lg bg-slate-50 px-3 py-3">
                  <p className="text-xl font-semibold text-slate-900">{value}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{label}</p>
                </div>
              ))}
            </div>
          );
        })()}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Resume Upload */}
          <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="text-base font-semibold text-slate-900">Upload Resume</h3>
              <AIStatusIndicator />
            </div>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition ${
                isDragging
                  ? "border-blue-400 bg-blue-50"
                  : "border-slate-200 bg-slate-50 hover:border-blue-300 hover:bg-blue-50/50"
              }`}
            >
              <svg
                className="mx-auto h-10 w-10 text-slate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                />
              </svg>
              <p className="mt-3 text-sm font-medium text-slate-700">
                {isDragging ? "Drop your file here" : "Drag & drop your resume"}
              </p>
              <p className="mt-1 text-xs text-slate-500">or click to browse — PDF, DOCX</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
            </div>
            {uploadMutation.isPending && (
              <p className="mt-3 text-xs text-blue-600 text-center animate-pulse">Uploading…</p>
            )}
            {uploadMutation.isError && (
              <p className="mt-3 text-xs text-red-600 text-center">
                {apiErrorMessage(uploadMutation.error, "Upload failed. Please try again.")}
              </p>
            )}
            {uploadMutation.isSuccess && (
              <p className="mt-3 text-xs text-emerald-600 text-center">Resume uploaded successfully!</p>
            )}
          </div>

          {/* Uploaded Resumes */}
          <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
            <h3 className="text-base font-semibold text-slate-900 mb-4">My Resumes</h3>
            {resumesQuery.isLoading ? (
              <SectionSkeleton rows={2} />
            ) : resumes.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No resumes uploaded yet.</p>
            ) : (
              <div className="space-y-3">
                {resumes.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => setSelectedResumeId(r.id)}
                    className={`flex cursor-pointer items-center justify-between rounded-xl p-3 ${
                      activeResumeId === r.id ? "bg-blue-50 ring-1 ring-blue-200" : "bg-slate-50"
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-900 truncate">{r.file_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-500">{r.file_type} · {(r.file_size / 1024).toFixed(0)} KB</span>
                      </div>
                    </div>
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        parseMutation.mutate(r.id);
                      }}
                      disabled={parseMutation.isPending}
                      className="ml-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1.5 text-xs font-medium transition disabled:opacity-50 shrink-0"
                    >
                      {parseMutation.isPending && parseMutation.variables === r.id ? "Parsing…" : "Parse with AI"}
                    </button>
                  </div>
                ))}
              </div>
            )}
            {parseMutation.isPending && (
              <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-4 w-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                  <p className="text-sm font-medium text-blue-800">Parsing Resume with AI...</p>
                </div>
                <div className="space-y-2">
                  {["Uploading to AI engine...", "Extracting skills...", "Extracting education...", "Analyzing experience...", "Building candidate profile..."].map((stepLabel, i) => (
                    <div key={stepLabel} className={`flex items-center gap-2 text-xs transition-all duration-300 ${i <= parseStep ? "text-blue-700" : "text-blue-400"}`}>
                      {i < parseStep ? (
                        <svg className="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : i === parseStep ? (
                        <div className="h-3.5 w-3.5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                      ) : (
                        <div className="h-3.5 w-3.5 rounded-full border border-blue-300" />
                      )}
                      {stepLabel}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {parseMutation.isError && (
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
                <p className="text-xs text-red-700">
                  {apiErrorMessage(parseMutation.error, "AI parsing failed. Please try again.")}
                </p>
                <button
                  onClick={() => activeResumeId && parseMutation.mutate(activeResumeId)}
                  className="mt-2 text-xs font-medium text-red-700 underline hover:text-red-800"
                >
                  Retry parsing
                </button>
              </div>
            )}
            {parseMutation.isSuccess && (
              <p className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                Resume parsed and candidate profile refreshed.
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Profile Sections */}
        <div className="lg:col-span-2 space-y-6">
          {profileQuery.isLoading ? (
            /* Loading state */
            <div className="space-y-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6 animate-pulse">
                  <div className="h-5 w-32 rounded bg-slate-200 mb-4" />
                  <SectionSkeleton />
                </div>
              ))}
            </div>
          ) : !profile ? (
            /* No profile yet — prompt to upload & parse */
            <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-12 text-center">
              <svg className="mx-auto h-14 w-14 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <h3 className="mt-4 text-lg font-semibold text-slate-900">Your profile is ready to be built</h3>
              <p className="mt-2 text-sm text-slate-500 max-w-sm mx-auto">
                {resumes.length === 0
                  ? "Upload your resume using the panel on the left, then click \"Parse with AI\" to generate your professional profile."
                  : "Click \"Parse with AI\" on your resume to generate your professional profile with skills, education, experience, and more."}
              </p>
            </div>
          ) : (
            /* Profile exists — render ONLY populated sections */
            <>
              {/* Skills */}
              {profile.skills && profile.skills.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {profile.skills.map((skill) => (
                      <div
                        key={skill.id}
                        className="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 border border-slate-100"
                      >
                        <span className="text-sm font-medium text-slate-800">{skill.skill_name}</span>
                        <ProficiencyBadge level={skill.proficiency_level} />
                        {skill.years_of_experience != null && (
                          <span className="text-xs text-slate-400">{skill.years_of_experience}y</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {profile.education && profile.education.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Education</h3>
                  <div className="space-y-4">
                    {profile.education.map((edu) => (
                      <div key={edu.id} className="flex gap-4 items-start">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600 shrink-0 mt-0.5">
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{edu.institution}</p>
                          {edu.degree && (
                            <p className="text-sm text-slate-600">
                              {edu.degree}
                              {edu.field_of_study ? ` in ${edu.field_of_study}` : ""}
                            </p>
                          )}
                          <p className="text-xs text-slate-500 mt-0.5">
                            {formatDate(edu.start_date)} — {formatDate(edu.end_date)}
                            {edu.gpa ? ` · GPA: ${edu.gpa}` : ""}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience */}
              {profile.experiences && profile.experiences.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Experience</h3>
                  <div className="space-y-5">
                    {profile.experiences.map((exp) => (
                      <div key={exp.id} className="relative pl-6 border-l-2 border-slate-200">
                        <div className="absolute -left-[5px] top-1 h-2 w-2 rounded-full bg-blue-600" />
                        <p className="text-sm font-medium text-slate-900">{exp.title}</p>
                        <p className="text-sm text-slate-600">
                          {exp.company}
                          {exp.location ? ` · ${exp.location}` : ""}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {formatDate(exp.start_date)} — {exp.is_current ? "Present" : formatDate(exp.end_date)}
                        </p>
                        {exp.description && (
                          <p className="mt-2 text-sm text-slate-600 leading-relaxed">{exp.description}</p>
                        )}
                        {exp.technologies && (
                          <p className="mt-1 text-xs text-slate-500">
                            <span className="font-medium">Tech:</span> {exp.technologies}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects */}
              {profile.projects && profile.projects.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm p-6">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Projects</h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {profile.projects.map((proj) => (
                      <div key={proj.id} className="rounded-xl bg-slate-50 border border-slate-100 p-4">
                        <div className="flex items-start justify-between">
                          <p className="text-sm font-medium text-slate-900">{proj.project_name}</p>
                          {proj.url && (
                            <a href={proj.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700 shrink-0 ml-2">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                              </svg>
                            </a>
                          )}
                        </div>
                        {proj.description && <p className="mt-1 text-xs text-slate-600 leading-relaxed">{proj.description}</p>}
                        {proj.year && <p className="mt-2 text-xs text-slate-500">{proj.year}</p>}
                        {proj.technologies && (
                          <p className="mt-2 text-xs text-slate-500"><span className="font-medium">Tech:</span> {proj.technologies}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications */}
              {profile.certifications && profile.certifications.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-900">Certifications</h3>
                  <div className="space-y-3">
                    {profile.certifications.map((cert) => (
                      <div key={cert.id} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">{cert.certification_name}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {[cert.issuing_organization, cert.issue_date].filter(Boolean).join(" · ")}
                        </p>
                        {cert.credential_url && (
                          <a href={cert.credential_url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs font-medium text-blue-600 hover:underline">
                            View credential
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Achievements */}
              {profile.achievements && profile.achievements.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-900">Achievements</h3>
                  <div className="space-y-3">
                    {profile.achievements.map((achievement, index) => (
                      <div key={`${achievement.title}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">{achievement.title}</p>
                        {achievement.date && <p className="mt-1 text-xs text-slate-500">{achievement.date}</p>}
                        {achievement.description && <p className="mt-2 text-sm text-slate-600">{achievement.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Internships */}
              {profile.internships && profile.internships.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-900">Internships</h3>
                  <div className="space-y-4">
                    {profile.internships.map((internship, index) => (
                      <div key={`${internship.company}-${internship.role}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">{internship.role}</p>
                        <p className="mt-1 text-sm text-slate-600">{internship.company}</p>
                        {(internship.duration || internship.start_date || internship.end_date) && (
                          <p className="mt-1 text-xs text-slate-500">
                            {internship.duration || [internship.start_date, internship.end_date].filter(Boolean).join(" - ")}
                          </p>
                        )}
                        {internship.description && <p className="mt-2 text-sm text-slate-600">{internship.description}</p>}
                        {internship.technologies?.length > 0 && (
                          <p className="mt-2 text-xs text-slate-500">Tech: {internship.technologies.join(", ")}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Research */}
              {profile.research_experience && profile.research_experience.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-900">Research</h3>
                  <div className="space-y-4">
                    {profile.research_experience.map((research, index) => (
                      <div key={`${research.title}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">{research.title}</p>
                        {research.duration && <p className="mt-1 text-xs text-slate-500">{research.duration}</p>}
                        {research.description && <p className="mt-2 text-sm leading-relaxed text-slate-600">{research.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Links */}
              {profile.links && profile.links.length > 0 && (
                <div className="rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-900">Links</h3>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {profile.links.map((link, index) => (
                      <a
                        key={`${link.url}-${index}`}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-lg border border-slate-200 bg-white p-3 text-sm font-medium text-blue-600 transition hover:bg-blue-50"
                      >
                        {link.label || link.link_type}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Awards, Publications & Languages */}
              {(profile.awards?.length > 0 || profile.publications?.length > 0 || profile.languages?.length > 0) && (
                <div className="rounded-lg border border-slate-200/90 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-900">Awards, Publications & Languages</h3>
                  <div className="space-y-4">
                    {profile.awards.map((award, index) => (
                      <div key={`${award.title}-${index}`}>
                        <p className="text-sm font-semibold text-slate-900">{award.title}</p>
                        <p className="text-xs text-slate-500">{[award.issuer, award.date].filter(Boolean).join(" · ")}</p>
                      </div>
                    ))}
                    {profile.publications.map((publication, index) => (
                      <div key={`${publication.title}-${index}`}>
                        <p className="text-sm font-semibold text-slate-900">{publication.title}</p>
                        <p className="text-xs text-slate-500">{[publication.publisher, publication.publication_date].filter(Boolean).join(" · ")}</p>
                      </div>
                    ))}
                    {profile.languages.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {profile.languages.map((language) => (
                          <span key={language} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{language}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
