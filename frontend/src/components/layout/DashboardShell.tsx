"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Sidebar from "@/components/layout/Sidebar";
import Navbar from "@/components/layout/Navbar";

interface DashboardShellProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  actions?: React.ReactNode;
}

export function DashboardShell({ children, title, description, actions }: DashboardShellProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F5F7FA]">
        <div className="flex flex-col items-center gap-3 rounded-lg border border-slate-200 bg-white px-8 py-7 shadow-sm">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />
          <p className="text-sm font-medium text-slate-500">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[#F5F7FA]">
      <Sidebar />
      <div className="transition-[padding] duration-200 md:pl-[272px]">
        <Navbar />
        <main className="mx-auto w-full max-w-[1500px] px-4 py-7 sm:px-6 lg:px-8">
          {(title || actions) && (
            <div className="mb-6 flex flex-col gap-4 border-b border-slate-200/80 pb-5 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                {title && <h2 className="text-[26px] font-semibold leading-tight tracking-tight text-slate-950">{title}</h2>}
                {description && <p className="mt-1.5 max-w-3xl text-sm leading-6 text-slate-500">{description}</p>}
              </div>
              {actions && <div className="flex shrink-0 flex-wrap items-center gap-2.5">{actions}</div>}
            </div>
          )}
          <div className="animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
