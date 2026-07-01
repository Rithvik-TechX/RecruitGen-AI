"use client";

import { useAIStatus } from "@/lib/hooks";

const styles = {
  ACTIVE: "border-emerald-200 bg-emerald-50 text-emerald-700",
  FALLBACK: "border-amber-200 bg-amber-50 text-amber-700",
  UNAVAILABLE: "border-red-200 bg-red-50 text-red-700",
};

const dots = {
  ACTIVE: "bg-emerald-500",
  FALLBACK: "bg-amber-500",
  UNAVAILABLE: "bg-red-500",
};

const labels = {
  ACTIVE: "Gemini Active",
  FALLBACK: "Fallback Mode",
  UNAVAILABLE: "AI Unavailable",
};

export function AIStatusIndicator() {
  const { data } = useAIStatus();
  const state = data?.state ?? "UNAVAILABLE";

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold ${styles[state]}`}>
      <span className={`h-2 w-2 rounded-full ${dots[state]}`} />
      {labels[state]}
    </div>
  );
}
