"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import Button from "@/components/ui/Button";

const ROLE_ROUTES: Record<string, string> = {
  admin: "/admin",
  recruiter: "/recruiter",
  candidate: "/candidate",
  hr_manager: "/hr",
};

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace(ROLE_ROUTES[user.role] || "/");
    }
  }, [user, router]);

  if (user) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      toast.success("Welcome back! Redirecting...");
    } catch (err) {
      const msg = getApiError(err, "Invalid email or password.");
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-[440px]">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600 text-sm font-semibold text-white shadow-sm">RG</div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">RecruitGen AI</h1>
          <p className="mt-2 text-sm text-slate-500">Sign in to your recruitment workspace</p>
        </div>

        <div className="app-card p-6 sm:p-8">
          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="form-label">Email address</label>
              <input id="email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="form-input" placeholder="you@company.com" />
            </div>
            <div>
              <label htmlFor="password" className="form-label">Password</label>
              <div className="relative">
                <input id="password" type={showPassword ? "text" : "password"} required value={password} onChange={(event) => setPassword(event.target.value)} className="form-input pr-20" placeholder="Enter password" />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-500 hover:text-slate-900">
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
            <Button type="submit" className="w-full" isLoading={loading}>
              Sign in
            </Button>
          </form>

          <div className="mt-6 border-t border-slate-200 pt-5 text-center text-sm text-slate-500">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-blue-600 hover:text-blue-700">
              Create account
            </Link>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">Secure access for recruiters, HR teams, admins, and candidates</p>
      </div>
    </main>
  );
}
