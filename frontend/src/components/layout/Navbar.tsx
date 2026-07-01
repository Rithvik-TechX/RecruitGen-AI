"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useUnreadCount, useNotifications, useMarkNotificationRead, useJobs } from "@/lib/hooks";
import type { Notification, Job } from "@/types";

const routeLabels: Record<string, string> = {
  "/recruiter": "Recruiter Dashboard",
  "/recruiter/jobs": "Jobs",
  "/recruiter/applications": "Applications",
  "/recruiter/rankings": "Candidate Rankings",
  "/recruiter/interviews": "Interviews",
  "/recruiter/analytics": "Analytics",
  "/recruiter/reports": "Reports",
  "/candidate": "Candidate Dashboard",
  "/candidate/profile": "Profile",
  "/candidate/jobs": "Find Jobs",
  "/candidate/applications": "Applications",
  "/candidate/interviews": "Interviews",
  "/candidate/notifications": "Notifications",
  "/admin": "Admin Dashboard",
  "/admin/users": "Users",
  "/admin/organizations": "Organizations",
  "/admin/analytics": "Platform Analytics",
  "/hr": "HR Dashboard",
  "/hr/candidates": "Candidates",
  "/hr/interviews": "Interviews",
  "/hr/recommendations": "Recommendations",
  "/hr/reports": "Reports",
};

/* ── Notification Icon Helpers ──────────────────────────── */
const NOTIF_STYLES: Record<string, { icon: string; color: string }> = {
  interview_invite: { icon: "📅", color: "bg-violet-100 text-violet-700" },
  shortlisted: { icon: "⭐", color: "bg-amber-100 text-amber-700" },
  rejection: { icon: "❌", color: "bg-red-100 text-red-700" },
  offer: { icon: "🎉", color: "bg-emerald-100 text-emerald-700" },
  application_update: { icon: "📋", color: "bg-blue-100 text-blue-700" },
  general: { icon: "🔔", color: "bg-slate-100 text-slate-700" },
};

function timeAgo(date: string): string {
  const diff = Date.now() - new Date(date).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/* ── Search Result Type ─────────────────────────────────── */
interface SearchResult {
  id: string;
  title: string;
  subtitle: string;
  category: "job" | "report" | "page";
  href: string;
}

export default function Navbar() {
  const { user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const unreadQuery = useUnreadCount();

  /* Notification State */
  const [showNotifs, setShowNotifs] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const notifQuery = useNotifications();
  const markRead = useMarkNotificationRead();

  /* Search State */
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const searchRef = useRef<HTMLDivElement>(null);
  const jobsQuery = useJobs();

  if (!user) return null;

  const title = routeLabels[pathname] ?? "Workspace";
  const unreadCount = unreadQuery.data?.count ?? 0;
  const notifications: Notification[] = notifQuery.data ?? [];

  /* Close dropdowns on outside click */
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setShowNotifs(false);
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setShowSearch(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  /* Search logic */
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    if (query.trim().length < 2) {
      setSearchResults([]);
      setShowSearch(false);
      return;
    }
    const q = query.toLowerCase();
    const results: SearchResult[] = [];

    // Search jobs
    const jobs: Job[] = jobsQuery.data ?? [];
    jobs.forEach((job) => {
      if (
        job.title.toLowerCase().includes(q) ||
        (job.department ?? "").toLowerCase().includes(q) ||
        (job.location ?? "").toLowerCase().includes(q)
      ) {
        results.push({
          id: job.id,
          title: job.title,
          subtitle: `${job.department ?? "General"} · ${job.status}`,
          category: "job",
          href: user.role === "candidate" ? "/candidate/jobs" : "/recruiter/jobs",
        });
      }
    });

    // Search pages
    const pages = Object.entries(routeLabels);
    pages.forEach(([href, label]) => {
      if (label.toLowerCase().includes(q)) {
        results.push({
          id: href,
          title: label,
          subtitle: "Page",
          category: "page",
          href,
        });
      }
    });

    setSearchResults(results.slice(0, 8));
    setShowSearch(results.length > 0 || query.trim().length >= 2);
  }, [jobsQuery.data, user.role]);

  const handleNotifClick = (notif: Notification) => {
    if (!notif.is_read) markRead.mutate(notif.id);
  };

  const toggleNotifs = () => {
    setShowNotifs((prev) => !prev);
    setShowSearch(false);
  };

  const categoryIcon: Record<string, string> = { job: "💼", report: "📊", page: "📄" };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/90 bg-white/95 backdrop-blur">
      <div className="flex h-[68px] items-center justify-between gap-4 px-5 sm:px-6">
        <div className="min-w-0 pl-12 md:pl-0">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">RecruitGen AI</p>
          <h1 className="truncate text-[18px] font-semibold tracking-tight text-slate-950">{title}</h1>
        </div>
        <div className="flex items-center gap-3">
          {/* ── Search ──────────────────────────────────── */}
          <div ref={searchRef} className="relative hidden lg:block">
            <div className="w-72 flex items-center rounded-lg border border-slate-200 bg-slate-50/90 px-3 text-slate-400 transition focus-within:border-blue-500 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-600/10">
              <svg className="mr-2 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
              <input
                className="h-10 w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
                placeholder="Search jobs, pages…"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => searchQuery.trim().length >= 2 && setShowSearch(true)}
              />
              {searchQuery && (
                <button onClick={() => { setSearchQuery(""); setShowSearch(false); }} className="text-slate-400 hover:text-slate-600">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            {/* Search Results Dropdown */}
            {showSearch && (
              <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden z-50">
                {searchResults.length > 0 ? (
                  <ul className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                    {searchResults.map((r) => (
                      <li key={r.id}>
                        <button
                          onClick={() => { router.push(r.href); setShowSearch(false); setSearchQuery(""); }}
                          className="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
                        >
                          <span className="text-lg">{categoryIcon[r.category] ?? "📄"}</span>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-slate-900">{r.title}</p>
                            <p className="truncate text-xs text-slate-500">{r.subtitle}</p>
                          </div>
                          <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 capitalize">{r.category}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="px-4 py-8 text-center">
                    <p className="text-sm text-slate-500">No results found for &ldquo;{searchQuery}&rdquo;</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Notification Bell ───────────────────────── */}
          <div ref={notifRef} className="relative hidden sm:block">
            <button
              onClick={toggleNotifs}
              className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:bg-slate-50 hover:text-slate-700"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022 23.848 23.848 0 0 0 5.455 1.31m5.714 0a3 3 0 1 1-5.714 0m5.714 0a24.255 24.255 0 0 1-5.714 0" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>

            {/* Notification Dropdown */}
            {showNotifs && (
              <div className="absolute right-0 top-full mt-2 w-96 rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden z-50">
                <div className="border-b border-slate-100 px-4 py-3 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
                  {unreadCount > 0 && (
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {unreadCount} unread
                    </span>
                  )}
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifQuery.isLoading ? (
                    <div className="p-6 space-y-3">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="animate-pulse flex gap-3">
                          <div className="h-9 w-9 rounded-full bg-slate-200 shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="h-3 w-3/4 rounded bg-slate-200" />
                            <div className="h-2.5 w-1/2 rounded bg-slate-100" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : notifQuery.isError ? (
                    <div className="p-8 text-center">
                      <p className="text-sm text-red-500">Failed to load notifications.</p>
                      <button
                        onClick={() => notifQuery.refetch()}
                        className="mt-2 text-xs font-medium text-blue-600 hover:text-blue-700"
                      >
                        Try again
                      </button>
                    </div>
                  ) : notifications.length === 0 ? (
                    <div className="p-8 text-center">
                      <span className="text-3xl">🔔</span>
                      <p className="mt-2 text-sm font-medium text-slate-700">All caught up!</p>
                      <p className="mt-1 text-xs text-slate-400">No notifications to show.</p>
                    </div>
                  ) : (
                    <ul className="divide-y divide-slate-50">
                      {notifications.slice(0, 20).map((n) => {
                        const style = NOTIF_STYLES[n.type] ?? NOTIF_STYLES.general;
                        return (
                          <li key={n.id}>
                            <button
                              onClick={() => handleNotifClick(n)}
                              className={`flex w-full gap-3 px-4 py-3.5 text-left transition hover:bg-slate-50 ${
                                !n.is_read ? "bg-blue-50/40" : ""
                              }`}
                            >
                              <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm ${style.color}`}>
                                {style.icon}
                              </span>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-start justify-between gap-2">
                                  <p className={`text-sm leading-snug ${!n.is_read ? "font-semibold text-slate-900" : "text-slate-700"}`}>
                                    {n.title}
                                  </p>
                                  {!n.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-600" />}
                                </div>
                                <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">{n.message}</p>
                                <p className="mt-1 text-[11px] text-slate-400">{timeAgo(n.created_at)}</p>
                              </div>
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
                {notifications.length > 0 && (
                  <div className="border-t border-slate-100 px-4 py-2.5">
                    <button
                      onClick={() => { router.push(`/${user.role === "candidate" ? "candidate" : user.role === "hr_manager" ? "hr" : "recruiter"}/notifications`); setShowNotifs(false); }}
                      className="w-full text-center text-xs font-medium text-blue-600 hover:text-blue-700 transition"
                    >
                      View all notifications
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── User Avatar ─────────────────────────────── */}
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 py-2 shadow-sm">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
              {user.full_name?.charAt(0)?.toUpperCase() ?? "U"}
            </div>
            <div className="hidden text-right md:block">
              <p className="max-w-36 truncate text-sm font-semibold text-slate-950">{user.full_name}</p>
              <p className="text-xs capitalize text-slate-500">{user.role.replace("_", " ")}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
