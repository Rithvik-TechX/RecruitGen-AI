"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useSidebarCounts } from "@/lib/hooks";

interface NavItem {
  label: string;
  href: string;
  section: string;
  icon: React.ReactNode;
}

function Icon({ path }: { path: string }) {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d={path} />
    </svg>
  );
}

const icons = {
  dashboard: <Icon path="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 8.25V6ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />,
  jobs: <Icon path="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25M8.25 6.144V5.25A2.25 2.25 0 0 1 10.5 3h3A2.25 2.25 0 0 1 15.75 5.25v.894M3.75 8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 12.826 0c1.069.16 1.837 1.094 1.837 2.175v3.783c0 .673-.302 1.31-.823 1.734A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.423-1.527a2.18 2.18 0 0 1-.827-1.734V8.706Z" />,
  applications: <Icon path="M9 12h6m-6 4h6m2.25 5.25H6.75A2.25 2.25 0 0 1 4.5 19V5A2.25 2.25 0 0 1 6.75 2.75h6.086c.597 0 1.169.237 1.591.659l3.164 3.164c.422.422.659.994.659 1.591V19a2.25 2.25 0 0 1-2.25 2.25Z" />,
  rankings: <Icon path="M3 13.5 8.25 18 21 6M5.25 6h13.5M5.25 10.5h7.5" />,
  interviews: <Icon path="M6.75 3v2.25M17.25 3v2.25M3.75 8.25h16.5M5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V6.75A2.25 2.25 0 0 0 18.75 4.5H5.25A2.25 2.25 0 0 0 3 6.75v12A2.25 2.25 0 0 0 5.25 21Z" />,
  analytics: <Icon path="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0 1 9.75 19.875V8.625ZM16.5 4.125C16.5 3.504 17.004 3 17.625 3h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />,
  reports: <Icon path="M19.5 14.25v-6A2.25 2.25 0 0 0 17.25 6H15A3.75 3.75 0 0 1 11.25 2.25H6.75A2.25 2.25 0 0 0 4.5 4.5v15A2.25 2.25 0 0 0 6.75 21.75h10.5a2.25 2.25 0 0 0 2.25-2.25v-5.25ZM12 3v3.75A2.25 2.25 0 0 0 14.25 9H18" />,
  users: <Icon path="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 20.25a6.75 6.75 0 0 1 13.5 0A12.3 12.3 0 0 1 9.75 22.5 12.3 12.3 0 0 1 3 20.25Z" />,
  profile: <Icon path="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.5 20.118a7.5 7.5 0 0 1 15 0A17.9 17.9 0 0 1 12 21.75a17.9 17.9 0 0 1-7.5-1.632Z" />,
  notifications: <Icon path="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022 23.848 23.848 0 0 0 5.455 1.31m5.714 0a3 3 0 1 1-5.714 0m5.714 0a24.255 24.255 0 0 1-5.714 0" />,
  organizations: <Icon path="M3.75 21h16.5M4.5 3h15M6 3v18M18 3v18M9 7.5h1.5M9 11.25h1.5M9 15h1.5M13.5 7.5H15M13.5 11.25H15M13.5 15H15" />,
};

const NAV_ITEMS: Record<string, NavItem[]> = {
  recruiter: [
    { label: "Overview", href: "/recruiter", section: "Workspace", icon: icons.dashboard },
    { label: "Jobs", href: "/recruiter/jobs", section: "Hiring", icon: icons.jobs },
    { label: "Applications", href: "/recruiter/applications", section: "Hiring", icon: icons.applications },
    { label: "Rankings", href: "/recruiter/rankings", section: "AI Intelligence", icon: icons.rankings },
    { label: "Interviews", href: "/recruiter/interviews", section: "AI Intelligence", icon: icons.interviews },
    { label: "Analytics", href: "/recruiter/analytics", section: "Reporting", icon: icons.analytics },
    { label: "Reports", href: "/recruiter/reports", section: "Reporting", icon: icons.reports },
  ],
  candidate: [
    { label: "Overview", href: "/candidate", section: "Workspace", icon: icons.dashboard },
    { label: "Profile", href: "/candidate/profile", section: "Candidate", icon: icons.profile },
    { label: "Find Jobs", href: "/candidate/jobs", section: "Candidate", icon: icons.jobs },
    { label: "Applications", href: "/candidate/applications", section: "Candidate", icon: icons.applications },
    { label: "Interviews", href: "/candidate/interviews", section: "Candidate", icon: icons.interviews },
    { label: "Notifications", href: "/candidate/notifications", section: "Updates", icon: icons.notifications },
  ],
  admin: [
    { label: "Overview", href: "/admin", section: "Platform", icon: icons.dashboard },
    { label: "Users", href: "/admin/users", section: "Management", icon: icons.users },
    { label: "Organizations", href: "/admin/organizations", section: "Management", icon: icons.organizations },
    { label: "Analytics", href: "/admin/analytics", section: "Reporting", icon: icons.analytics },
  ],
  hr_manager: [
    { label: "Overview", href: "/hr", section: "Workspace", icon: icons.dashboard },
    { label: "Candidates", href: "/hr/candidates", section: "Evaluation", icon: icons.users },
    { label: "Interviews", href: "/hr/interviews", section: "Evaluation", icon: icons.interviews },
    { label: "Recommendations", href: "/hr/recommendations", section: "Decision Support", icon: icons.rankings },
    { label: "Reports", href: "/hr/reports", section: "Decision Support", icon: icons.reports },
  ],
};

const ROLE_LABELS: Record<string, string> = {
  recruiter: "Recruiting",
  candidate: "Candidate Portal",
  admin: "Platform Admin",
  hr_manager: "HR Manager",
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data: counts } = useSidebarCounts();

  if (!user) return null;

  const countMap: Record<string, number> = {};
  if (counts && user) {
    if (user.role === "recruiter") {
      countMap["/recruiter/applications"] = counts.applications || 0;
    } else if (user.role === "hr_manager") {
      countMap["/hr/candidates"] = counts.candidates || 0;
      countMap["/hr/interviews"] = counts.interviews || 0;
    } else if (user.role === "candidate") {
      countMap["/candidate/jobs"] = counts.jobs || 0;
      countMap["/candidate/applications"] = counts.applications || 0;
      countMap["/candidate/notifications"] = counts.notifications || 0;
    } else if (user.role === "admin") {
      countMap["/admin/users"] = counts.users || 0;
    }
  }

  const items = NAV_ITEMS[user.role] || [];
  const grouped = items.reduce<Record<string, NavItem[]>>((acc, item) => {
    acc[item.section] = [...(acc[item.section] || []), item];
    return acc;
  }, {});

  const isActive = (href: string) => {
    const roleRoot = `/${user.role === "hr_manager" ? "hr" : user.role}`;
    return href === roleRoot ? pathname === href : pathname.startsWith(href);
  };

  const navContent = (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-[68px] items-center gap-3 border-b border-slate-200/90 px-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-sm font-semibold text-white shadow-sm">RG</div>
        <div className="min-w-0">
          <p className="truncate text-base font-semibold tracking-tight text-slate-950">RecruitGen AI</p>
          <p className="truncate text-xs font-medium text-slate-500">{ROLE_LABELS[user.role] ?? user.role}</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5">
        {Object.entries(grouped).map(([section, sectionItems]) => (
          <div key={section} className="mb-5">
            <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400">{section}</p>
            <div className="space-y-1">
              {sectionItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition ${
                      active
                        ? "bg-blue-50 text-blue-700 shadow-[inset_3px_0_0_#0A66C2]"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                    }`}
                  >
                    <span className={active ? "text-blue-600" : "text-slate-400"}>{item.icon}</span>
                    <span className="flex-1">{item.label}</span>
                    {(countMap[item.href] ?? 0) > 0 && (
                      <span className={`ml-auto inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[10px] font-bold ${
                        item.href.includes("notifications")
                          ? "bg-red-500 text-white"
                          : "bg-blue-100 text-blue-700"
                      }`}>
                        {countMap[item.href]}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-200/90 p-4">
        <div className="mb-3 flex items-center gap-3 rounded-lg bg-slate-50 p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">
            {user.full_name?.charAt(0)?.toUpperCase() ?? "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-950">{user.full_name}</p>
            <p className="truncate text-xs text-slate-500">{user.email}</p>
          </div>
        </div>
        <button onClick={logout} className="flex h-10 w-full items-center justify-center rounded-lg border border-slate-300 bg-white text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[272px] border-r border-slate-200/90 bg-white md:block">
        {navContent}
      </aside>
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-3 z-50 flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-sm md:hidden"
        aria-label="Open navigation"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button className="absolute inset-0 bg-slate-900/30" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full w-[300px] shadow-2xl">{navContent}</div>
        </div>
      )}
    </>
  );
}
