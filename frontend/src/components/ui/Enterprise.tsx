"use client";

import Link from "next/link";

type Tone = "blue" | "green" | "amber" | "red" | "slate" | "violet";

const toneMap: Record<Tone, { bg: string; text: string; bar: string }> = {
  blue: { bg: "bg-blue-50", text: "text-blue-700", bar: "bg-blue-600" },
  green: { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-600" },
  amber: { bg: "bg-amber-50", text: "text-amber-700", bar: "bg-amber-500" },
  red: { bg: "bg-red-50", text: "text-red-700", bar: "bg-red-600" },
  slate: { bg: "bg-slate-100", text: "text-slate-700", bar: "bg-slate-500" },
  violet: { bg: "bg-violet-50", text: "text-violet-700", bar: "bg-violet-600" },
};

export function PageGrid({ children, columns = "xl:grid-cols-4" }: { children: React.ReactNode; columns?: string }) {
  return <div className={`grid gap-4 sm:grid-cols-2 ${columns}`}>{children}</div>;
}

export function Section({
  title,
  description,
  action,
  children,
  className = "",
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`app-section ${className}`}>
      {(title || action) && (
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-950">{title}</h3>}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatCard({
  label,
  value,
  caption,
  tone = "blue",
}: {
  label: string;
  value: string | number;
  caption?: string;
  tone?: Tone;
}) {
  return (
    <div className="app-card p-5">
      <div className={`mb-4 h-1 w-10 rounded-full ${toneMap[tone].bar}`} />
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
      {caption && <p className="mt-1 text-xs text-slate-500">{caption}</p>}
    </div>
  );
}

export function StatusPill({ label, tone = "slate" }: { label: string; tone?: Tone }) {
  const toneClass = toneMap[tone];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize ${toneClass.bg} ${toneClass.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${toneClass.bar}`} />
      {label.replace(/_/g, " ")}
    </span>
  );
}

export function Toolbar({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`mb-5 flex flex-col gap-3 rounded-lg border border-slate-200/90 bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between ${className}`}>{children}</div>;
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="app-card flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
        <span className="text-lg font-semibold">RG</span>
      </div>
      <h3 className="text-base font-semibold text-slate-950">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function SearchField({
  value,
  onChange,
  placeholder = "Search",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="relative w-full md:max-w-sm">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
      </span>
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="form-input pl-9" />
    </div>
  );
}

export function PrimaryLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="inline-flex h-10 items-center justify-center rounded-lg bg-blue-600 px-4 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700">
      {children}
    </Link>
  );
}

export function ProgressBar({ value, tone = "blue" }: { value: number; tone?: Tone }) {
  const bounded = Math.max(0, Math.min(100, value));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full rounded-full ${toneMap[tone].bar}`} style={{ width: `${bounded}%` }} />
    </div>
  );
}
