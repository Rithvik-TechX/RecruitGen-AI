"use client";

import React, { createContext, useCallback, useContext, useState, useRef, useEffect } from "react";

/* ── Types ──────────────────────────────────────────────── */
type ToastType = "success" | "error" | "warning" | "info" | "loading";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
  exiting?: boolean;
}

interface ToastContextType {
  toast: {
    success: (message: string, duration?: number) => string;
    error: (message: string, duration?: number) => string;
    warning: (message: string, duration?: number) => string;
    info: (message: string, duration?: number) => string;
    loading: (message: string) => string;
  };
  dismiss: (id: string) => void;
  dismissAll: () => void;
  update: (id: string, type: ToastType, message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const MAX_TOASTS = 5;
const DEFAULT_DURATIONS: Record<ToastType, number> = {
  success: 4000,
  error: 0,
  warning: 5000,
  info: 4000,
  loading: 0,
};

let toastCounter = 0;

/* ── Icons ─────────────────────────────────────────────── */
function SuccessIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}
function ErrorIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}
function WarningIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  );
}
function InfoIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  );
}
function LoadingIcon() {
  return (
    <svg className="h-5 w-5 shrink-0 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
function CloseIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

const TOAST_STYLES: Record<ToastType, { bg: string; border: string; text: string; icon: React.ReactNode }> = {
  success: { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-800", icon: <SuccessIcon /> },
  error:   { bg: "bg-red-50",     border: "border-red-300",     text: "text-red-800",     icon: <ErrorIcon /> },
  warning: { bg: "bg-amber-50",   border: "border-amber-300",   text: "text-amber-800",   icon: <WarningIcon /> },
  info:    { bg: "bg-blue-50",    border: "border-blue-300",    text: "text-blue-800",    icon: <InfoIcon /> },
  loading: { bg: "bg-blue-50",    border: "border-blue-300",    text: "text-blue-800",    icon: <LoadingIcon /> },
};

/* ── Provider ──────────────────────────────────────────── */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    const timer = timersRef.current.get(id);
    if (timer) { clearTimeout(timer); timersRef.current.delete(id); }
    setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)));
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 300);
  }, []);

  const dismissAll = useCallback(() => {
    timersRef.current.forEach((timer) => clearTimeout(timer));
    timersRef.current.clear();
    setToasts([]);
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string, duration?: number): string => {
      const id = `toast-${++toastCounter}`;
      const dur = duration ?? DEFAULT_DURATIONS[type];
      setToasts((prev) => {
        const next = [...prev, { id, type, message, duration: dur }];
        return next.length > MAX_TOASTS ? next.slice(next.length - MAX_TOASTS) : next;
      });
      if (dur > 0) {
        const timer = setTimeout(() => dismiss(id), dur);
        timersRef.current.set(id, timer);
      }
      return id;
    },
    [dismiss],
  );

  const update = useCallback(
    (id: string, type: ToastType, message: string, duration?: number) => {
      const timer = timersRef.current.get(id);
      if (timer) { clearTimeout(timer); timersRef.current.delete(id); }
      setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, type, message, duration: duration ?? DEFAULT_DURATIONS[type] } : t)));
      const dur = duration ?? DEFAULT_DURATIONS[type];
      if (dur > 0) {
        const newTimer = setTimeout(() => dismiss(id), dur);
        timersRef.current.set(id, newTimer);
      }
    },
    [dismiss],
  );

  const toast = {
    success: (msg: string, dur?: number) => addToast("success", msg, dur),
    error:   (msg: string, dur?: number) => addToast("error", msg, dur),
    warning: (msg: string, dur?: number) => addToast("warning", msg, dur),
    info:    (msg: string, dur?: number) => addToast("info", msg, dur),
    loading: (msg: string) => addToast("loading", msg, 0),
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer));
    };
  }, []);

  return (
    <ToastContext.Provider value={{ toast, dismiss, dismissAll, update }}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none" style={{ maxWidth: "420px" }}>
        {toasts.map((t) => {
          const style = TOAST_STYLES[t.type];
          return (
            <div
              key={t.id}
              className={`pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 shadow-lg backdrop-blur-sm transition-all duration-300 ${
                t.exiting
                  ? "translate-x-[120%] opacity-0"
                  : "translate-x-0 opacity-100 animate-[slideIn_0.3s_ease-out]"
              } ${style.bg} ${style.border} ${style.text}`}
              role="alert"
            >
              {style.icon}
              <p className="flex-1 text-sm font-medium leading-snug">{t.message}</p>
              {t.type !== "loading" && (
                <button
                  onClick={() => dismiss(t.id)}
                  className="shrink-0 rounded-lg p-0.5 opacity-60 hover:opacity-100 transition-opacity"
                  aria-label="Dismiss"
                >
                  <CloseIcon />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
