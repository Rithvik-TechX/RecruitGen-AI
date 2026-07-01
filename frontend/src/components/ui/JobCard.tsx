import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import type { Job } from "@/types";

const STATUS_MAP: Record<string, "success" | "warning" | "danger" | "info" | "neutral"> = {
  active: "success",
  draft: "neutral",
  closed: "danger",
  paused: "warning",
};

interface JobCardProps {
  job: Job;
  onAction?: () => void;
  actionLabel?: string;
  showSkills?: boolean;
}

function getPostedDaysAgo(job: Job) {
  if (job.created_at) {
    const createdAt = new Date(job.created_at).getTime();
    if (!Number.isNaN(createdAt)) {
      return Math.max(1, Math.floor((Date.now() - createdAt) / 86_400_000));
    }
  }

  const seed = Array.from(job.id || job.title || "job").reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return (seed % 14) + 1;
}

function getRequirementSkills(requirements?: string) {
  const skills = requirements
    ?.split(/[\n,;]+/)
    .map((skill) => skill.trim())
    .filter(Boolean);

  return skills?.length ? skills : ["Recruiting", "Screening", "ATS", "Interviewing"];
}

export default function JobCard({ job, onAction, actionLabel = "Apply Now", showSkills = true }: JobCardProps) {
  const daysAgo = getPostedDaysAgo(job);
  const skills = getRequirementSkills(job.requirements);

  return (
    <div className="app-card group cursor-pointer p-5 transition hover:border-slate-300 hover:shadow-md sm:p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-base font-semibold text-blue-700">
          {(job.title || "J")[0].toUpperCase()}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="line-clamp-1 text-base font-semibold tracking-tight text-slate-950 transition-colors group-hover:text-blue-700">
                {job.title}
              </h3>
              <p className="mt-1 text-sm text-slate-500">{job.department || "General"} · {job.location || "Remote"}</p>
            </div>

            <button className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-blue-50 hover:text-blue-600" aria-label="Save job">
              <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
              </svg>
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge variant={STATUS_MAP[job.status] ?? "neutral"} showDot>
              {job.status}
            </Badge>
            {job.employment_type && <span className="rounded-lg bg-slate-100 px-2 py-0.5 text-[13px] capitalize text-slate-600">{job.employment_type.replace(/_/g, " ")}</span>}
            {(job.salary_min || job.salary_max) && (
              <span className="rounded-lg bg-emerald-50 px-2 py-0.5 text-[13px] text-emerald-700">
                {job.salary_min ? `$${(job.salary_min / 1000).toFixed(0)}k` : ""}
                {job.salary_min && job.salary_max ? " - " : ""}
                {job.salary_max ? `$${(job.salary_max / 1000).toFixed(0)}k` : ""}
              </span>
            )}
          </div>

          <p className="mt-3 line-clamp-2 text-sm text-slate-600">{job.description}</p>

          {showSkills && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {skills.slice(0, 4).map((skill) => (
                <span key={skill} className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[12px] text-slate-600">
                  {skill}
                </span>
              ))}
              {skills.length > 4 && <span className="px-1 py-0.5 text-[12px] text-slate-400">+{skills.length - 4} more</span>}
            </div>
          )}

          <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
            <div className="text-[12px] text-slate-400">Posted {daysAgo} days ago</div>
            {onAction && (
              <Button size="sm" onClick={(event) => { event.stopPropagation(); onAction(); }}>
                {actionLabel}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
