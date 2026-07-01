"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { DashboardShell } from "@/components/layout/DashboardShell";
import api from "@/lib/api";
import type { Organization } from "@/types";

interface OrganizationListResponse {
  organizations: Organization[];
  total_count: number;
}

interface OrganizationForm {
  name: string;
  industry: string;
  company_size: string;
}

const emptyForm: OrganizationForm = {
  name: "",
  industry: "",
  company_size: "",
};

function industryStyle(industry?: string): { bg: string; text: string } {
  const normalized = (industry || "").toLowerCase();
  if (normalized.includes("finance")) return { bg: "bg-amber-50", text: "text-amber-700" };
  if (normalized.includes("health")) return { bg: "bg-rose-50", text: "text-rose-700" };
  if (normalized.includes("human")) return { bg: "bg-emerald-50", text: "text-emerald-700" };
  if (normalized.includes("data") || normalized.includes("ai")) return { bg: "bg-violet-50", text: "text-violet-700" };
  if (normalized.includes("saas") || normalized.includes("tech")) return { bg: "bg-blue-50", text: "text-blue-700" };
  return { bg: "bg-slate-50", text: "text-slate-700" };
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function SkeletonCard() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="animate-pulse space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-slate-100" />
          <div className="space-y-2">
            <div className="h-4 w-36 rounded bg-slate-200" />
            <div className="h-3 w-24 rounded bg-slate-100" />
          </div>
        </div>
        <div className="h-3 w-full rounded bg-slate-100" />
        <div className="h-3 w-2/3 rounded bg-slate-100" />
      </div>
    </div>
  );
}

export default function AdminOrganizationsPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState<OrganizationForm>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const organizationsQuery = useQuery<OrganizationListResponse>({
    queryKey: ["organizations"],
    queryFn: async () => {
      const res = await api.get<OrganizationListResponse>("/organizations/");
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: OrganizationForm) => {
      const res = await api.post<Organization>("/organizations/", {
        name: payload.name.trim(),
        industry: payload.industry.trim() || null,
        company_size: payload.company_size.trim() || null,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
      setShowAddModal(false);
      setForm(emptyForm);
      setFormError(null);
    },
  });

  const organizations = useMemo(
    () => organizationsQuery.data?.organizations ?? [],
    [organizationsQuery.data?.organizations],
  );
  const totalMembers = useMemo(
    () => organizations.reduce((sum, org) => sum + (org.member_count ?? 0), 0),
    [organizations],
  );

  const submit = () => {
    if (!form.name.trim()) {
      setFormError("Organization name is required.");
      return;
    }
    setFormError(null);
    createMutation.mutate(form);
  };

  return (
    <DashboardShell
      title="Organization Management"
      description="Manage employer accounts and tenant records."
      actions={
        <button
          onClick={() => setShowAddModal(true)}
          className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          Add Organization
        </button>
      }
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Organizations</p>
          <p className="mt-1 text-2xl font-semibold text-slate-950">
            {organizationsQuery.data?.total_count ?? organizations.length}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Members</p>
          <p className="mt-1 text-2xl font-semibold text-slate-950">{totalMembers}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Status</p>
          <p className="mt-1 text-2xl font-semibold text-emerald-600">Active</p>
        </div>
      </div>

      {organizationsQuery.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : organizationsQuery.isError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          Failed to load organizations. Please refresh after confirming the backend is healthy.
        </div>
      ) : organizations.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center shadow-sm">
          <p className="text-base font-medium text-slate-800">No organizations found</p>
          <p className="mt-1 text-sm text-slate-500">Create an organization to start onboarding users.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {organizations.map((org) => {
            const style = industryStyle(org.industry);
            return (
              <div key={org.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${style.bg}`}>
                      <svg className={`h-5 w-5 ${style.text}`} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                      </svg>
                    </div>
                    <div className="min-w-0">
                      <h3 className="truncate font-semibold text-slate-950">{org.name}</h3>
                      <p className="text-xs text-slate-500">{org.company_size || "Company size not set"}</p>
                    </div>
                  </div>
                  <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}>
                    {org.industry || "General"}
                  </span>
                </div>
                <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                  <span className="text-sm font-medium text-slate-700">{org.member_count ?? 0} members</span>
                  <span className="text-xs text-slate-400">{formatDate(org.created_at)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-950">Add Organization</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                aria-label="Close"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4 p-6">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Organization Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder="Acme Corp"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Industry</label>
                <input
                  type="text"
                  value={form.industry}
                  onChange={(e) => setForm({ ...form, industry: e.target.value })}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder="Technology"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Company Size</label>
                <input
                  type="text"
                  value={form.company_size}
                  onChange={(e) => setForm({ ...form, company_size: e.target.value })}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  placeholder="51-200"
                />
              </div>
              {formError && <p className="text-sm text-red-600">{formError}</p>}
              {createMutation.isError && (
                <p className="text-sm text-red-600">Could not create organization. Check for duplicate names.</p>
              )}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  onClick={submit}
                  disabled={createMutation.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? "Adding..." : "Add Organization"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
