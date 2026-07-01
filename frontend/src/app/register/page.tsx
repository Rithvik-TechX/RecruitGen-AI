"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { getApiError } from "@/lib/utils";
import Button from "@/components/ui/Button";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register({ email, password, full_name: fullName, role: "candidate", organization_name: "RecruitGen" });
      toast.success("Account created successfully! Welcome aboard.");
      router.push("/candidate");
    } catch (err) {
      const msg = getApiError(err, "Registration failed. Email may already be in use.");
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600 text-sm font-semibold text-white shadow-sm">RG</div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Create your account</h1>
          <p className="mt-2 text-sm text-slate-500">Register as a candidate to find jobs and manage applications</p>
        </div>

        <div className="app-card p-6 sm:p-8">
          {error && <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="fullName" className="form-label">Full name</label>
              <input id="fullName" required value={fullName} onChange={(e) => setFullName(e.target.value)} className="form-input" placeholder="Your full name" />
            </div>
            <div>
              <label htmlFor="email" className="form-label">Email address</label>
              <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="form-input" placeholder="you@example.com" />
            </div>
            <div>
              <label htmlFor="password" className="form-label">Password</label>
              <input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="form-input" placeholder="Minimum 8 characters" />
            </div>

            <div className="rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
                </svg>
                <p className="text-sm text-blue-800">
                  <span className="font-semibold">Candidate account.</span>{" "}
                  Recruiter and HR accounts are created by administrators.
                </p>
              </div>
            </div>

            <Button type="submit" className="w-full" isLoading={loading}>
              Create candidate account
            </Button>
          </form>

          <div className="mt-6 border-t border-slate-200 pt-5 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-blue-600 hover:text-blue-700">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
