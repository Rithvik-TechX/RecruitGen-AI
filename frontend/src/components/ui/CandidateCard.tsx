import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";

interface CandidateCardProps {
  name: string;
  role?: string;
  experience?: string;
  status?: string;
  highlights?: string[];
  actionLabel?: string;
  onAction?: () => void;
  matchScore?: number;
}

const STATUS_MAP: Record<string, "success" | "warning" | "danger" | "info" | "neutral"> = {
  applied: "warning",
  screened: "info",
  shortlisted: "success",
  interview_scheduled: "info",
  interview_completed: "info",
  rejected: "danger",
  selected: "success",
};

function fallbackMatchScore(name: string) {
  const seed = Array.from(name).reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return (seed % 40) + 60;
}

export default function CandidateCard({
  name,
  role,
  experience,
  status,
  highlights,
  actionLabel = "View Profile",
  onAction,
  matchScore = fallbackMatchScore(name),
}: CandidateCardProps) {
  const ringColor = matchScore >= 85 ? "text-emerald-600" : matchScore >= 70 ? "text-amber-500" : "text-slate-300";

  return (
    <div className="app-card p-5 transition hover:border-slate-300 hover:shadow-md sm:p-6">
      <div className="flex flex-col gap-5 sm:flex-row">
        <div className="flex shrink-0 flex-col items-center gap-3">
          <div className="relative">
            <div className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-white bg-blue-50 text-xl font-semibold text-blue-700 shadow-sm">
              {name.charAt(0).toUpperCase()}
            </div>
            <div className="absolute -inset-1 rounded-full border-[3px] border-slate-100" />
            <svg className="absolute -inset-1 h-[72px] w-[72px] -rotate-90" viewBox="0 0 72 72">
              <circle cx="36" cy="36" r="34" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="213" strokeDashoffset={213 - (213 * matchScore) / 100} className={ringColor} />
            </svg>
            <div className="absolute -bottom-2 -right-2 rounded-full border border-slate-100 bg-white px-1.5 py-0.5 shadow-sm">
              <span className={`text-[11px] font-semibold ${ringColor}`}>{matchScore}%</span>
            </div>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold tracking-tight text-slate-950">{name}</h3>
              <p className="mt-0.5 text-sm text-slate-500">{[role, experience].filter(Boolean).join(" · ")}</p>
            </div>
            {status && <Badge variant={STATUS_MAP[status] ?? "neutral"} showDot>{status}</Badge>}
          </div>

          {highlights && highlights.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {highlights.map((highlight) => (
                <span key={highlight} className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[12px] font-medium text-slate-600">
                  {highlight}
                </span>
              ))}
            </div>
          )}

          <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
            <p className="text-[12px] text-slate-400">Recently updated</p>
            {onAction && (
              <Button size="sm" variant="secondary" onClick={onAction}>
                {actionLabel}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
