"use client";

import { useState, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useMarkSectionSeen } from "@/lib/hooks";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { User, UserRole } from "@/types";

function roleBadge(role: UserRole): { label: string; className: string } {
  const map: Record<UserRole, { label: string; className: string }> = {
    admin: { label: "Admin", className: "bg-purple-50 text-purple-700" },
    recruiter: { label: "Recruiter", className: "bg-blue-50 text-blue-700" },
    candidate: { label: "Candidate", className: "bg-emerald-50 text-emerald-700" },
    hr_manager: { label: "HR Manager", className: "bg-orange-50 text-orange-700" },
  };
  return map[role] ?? { label: role, className: "bg-slate-100 text-slate-700" };
}

const defaultCreateForm = {
  full_name: "",
  email: "",
  password: "",
  role: "recruiter" as UserRole,
  organization_name: "RecruitGen",
};

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [createForm, setCreateForm] = useState(defaultCreateForm);
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const markSeen = useMarkSectionSeen();
  useEffect(() => { markSeen.mutate("admin_users"); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleMutation = useMutation({
    mutationFn: async (userId: string) => {
      const res = await api.patch(`/users/${userId}/toggle-active`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User status updated.");
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to update user status."));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/users/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User permanently removed.");
      setUserToDelete(null);
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to remove user."));
    },
  });

  const { data: users = [], isLoading } = useQuery<User[]>({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const response = await api.get<User[]>("/users/");
      return response.data;
    },
  });

  const createUserMutation = useMutation({
    mutationFn: async (payload: typeof defaultCreateForm) => {
      const res = await api.post("/auth/admin/create-user", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User account created successfully!");
      setShowCreateModal(false);
      setCreateForm(defaultCreateForm);
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to create user account."));
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.full_name.trim()) { toast.warning("Please enter a full name."); return; }
    if (!createForm.email.trim()) { toast.warning("Please enter an email address."); return; }
    if (createForm.password.length < 8) { toast.warning("Password must be at least 8 characters."); return; }
    createUserMutation.mutate(createForm);
  };

  const filteredUsers = users.filter(
    (user) =>
      user.full_name.toLowerCase().includes(search.toLowerCase()) ||
      user.email.toLowerCase().includes(search.toLowerCase()) ||
      user.role.toLowerCase().includes(search.toLowerCase())
  );

  const roleCounts = users.reduce((acc, u) => {
    acc[u.role] = (acc[u.role] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <DashboardShell
      title="User Management"
      description="Manage user accounts, roles, and access privileges."
      actions={
        <button
          onClick={() => setShowCreateModal(true)}
          className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          + Create User
        </button>
      }
    >
      {/* Role Summary */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Admins", count: roleCounts.admin ?? 0, color: "text-purple-700 bg-purple-50 border-purple-200" },
          { label: "Recruiters", count: roleCounts.recruiter ?? 0, color: "text-blue-700 bg-blue-50 border-blue-200" },
          { label: "HR Managers", count: roleCounts.hr_manager ?? 0, color: "text-orange-700 bg-orange-50 border-orange-200" },
          { label: "Candidates", count: roleCounts.candidate ?? 0, color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
        ].map((item) => (
          <div key={item.label} className={`rounded-lg border p-4 ${item.color}`}>
            <p className="text-2xl font-semibold">{item.count}</p>
            <p className="text-xs font-medium opacity-80">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="mb-6 rounded-lg border border-slate-200/90 bg-white shadow-sm p-4">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input
            type="text"
            placeholder="Search by name, email, or role…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
          />
        </div>
      </div>

      {/* Users Table */}
      <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-4 animate-pulse">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="h-9 w-9 rounded-full bg-slate-200" />
                  <div className="h-4 w-48 rounded bg-slate-200" />
                  <div className="h-4 w-32 rounded bg-slate-100" />
                  <div className="h-5 w-20 rounded-full bg-slate-200" />
                </div>
              ))}
            </div>
          ) : (
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Joined</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filteredUsers.map((user) => {
                  const rb = roleBadge(user.role);
                  return (
                    <tr key={user.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-blue-700">
                            {user.full_name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                          </div>
                          <span className="font-medium text-slate-900">{user.full_name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{user.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${rb.className}`}>
                          {rb.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.is_active ? (
                          <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-emerald-400" />
                            <span className="text-sm text-emerald-600 font-medium">Active</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-slate-300" />
                            <span className="text-sm text-slate-500 font-medium">Inactive</span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        {new Date(user.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex justify-end gap-2">
                          {user.role !== "admin" && (
                            <>
                              <button
                                onClick={() => toggleMutation.mutate(user.id)}
                                disabled={toggleMutation.isPending || deleteMutation.isPending}
                                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition ${
                                  user.is_active
                                    ? "text-red-600 bg-red-50 hover:bg-red-100 border border-red-200"
                                    : "text-emerald-600 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200"
                                } disabled:opacity-50`}
                              >
                                {user.is_active ? "Disable" : "Enable"}
                              </button>
                              <button
                                onClick={() => setUserToDelete(user)}
                                disabled={deleteMutation.isPending}
                                className="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-700 transition hover:bg-red-50 disabled:opacity-50"
                              >
                                Remove
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
        {!isLoading && filteredUsers.length === 0 && (
          <div className="p-12 text-center">
            <svg className="mx-auto h-10 w-10 text-slate-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <p className="mt-3 text-sm text-slate-500">No users match your search.</p>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Create User Account</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600 transition">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={createForm.full_name}
                  onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="John Smith"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="user@company.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="Minimum 8 characters"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                <select
                  value={createForm.role}
                  onChange={(e) => setCreateForm({ ...createForm, role: e.target.value as UserRole })}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                >
                  <option value="recruiter">Recruiter</option>
                  <option value="hr_manager">HR Manager</option>
                </select>
                <p className="mt-1.5 text-xs text-slate-500">
                  Only Recruiter and HR Manager accounts can be created here. Candidates register themselves.
                </p>
              </div>
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createUserMutation.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {createUserMutation.isPending ? "Creating…" : "Create Account"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Permanent Delete Modal */}
      {userToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-slate-900">Remove User Permanently</h3>
              <p className="mt-1 text-sm text-slate-500">
                This action cannot be undone.
              </p>
            </div>
            <div className="p-6">
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-900">
                  Permanently remove <span className="font-semibold">{userToDelete.full_name}</span>?
                </p>
                <p className="mt-1 break-all text-xs text-red-700">{userToDelete.email}</p>
              </div>
              <div className="mt-6 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setUserToDelete(null)}
                  disabled={deleteMutation.isPending}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(userToDelete.id)}
                  disabled={deleteMutation.isPending}
                  className="rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-red-700 disabled:opacity-50"
                >
                  {deleteMutation.isPending ? "Removing..." : "Remove Permanently"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
