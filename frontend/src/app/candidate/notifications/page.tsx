"use client";

import { useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { useMarkAllNotificationsRead } from "@/lib/hooks";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Notification, NotificationType } from "@/types";

function useNotifications() {
  return useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await api.get<{ notifications: Notification[]; unread_count: number; total_count: number }>("/notifications/");
      return res.data.notifications;
    },
  });
}

function formatTimeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function NotificationIcon({ type }: { type: NotificationType }) {
  const iconMap: Record<NotificationType, { bg: string; icon: React.ReactNode }> = {
    interview_invite: {
      bg: "bg-blue-50 text-blue-600",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
        </svg>
      ),
    },
    shortlisted: {
      bg: "bg-emerald-50 text-emerald-600",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    rejection: {
      bg: "bg-red-50 text-red-600",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    offer: {
      bg: "bg-amber-50 text-amber-600",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
        </svg>
      ),
    },
    application_update: {
      bg: "bg-indigo-50 text-indigo-600",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
        </svg>
      ),
    },
    general: {
      bg: "bg-slate-50 text-slate-600",
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
      ),
    },
  };

  const config = iconMap[type] ?? iconMap.general;
  return (
    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${config.bg} shrink-0`}>
      {config.icon}
    </div>
  );
}

function SkeletonNotification() {
  return (
    <div className="flex items-start gap-4 p-5 animate-pulse">
      <div className="h-10 w-10 rounded-xl bg-slate-200 shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-48 rounded bg-slate-200" />
        <div className="h-3 w-64 rounded bg-slate-100" />
      </div>
      <div className="h-3 w-12 rounded bg-slate-100 shrink-0" />
    </div>
  );
}

export default function CandidateNotificationsPage() {
  const queryClient = useQueryClient();
  const notificationsQuery = useNotifications();
  const notifications: Notification[] = notificationsQuery.data ?? [];
  const markAllRead = useMarkAllNotificationsRead();
  useEffect(() => { markAllRead.mutate(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markAsReadMutation = useMutation({
    mutationFn: async (notificationId: string) => {
      await api.patch(`/notifications/${notificationId}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const handleClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsReadMutation.mutate(notification.id);
    }
  };

  return (
    <DashboardShell
      title="Notifications"
      description="Stay updated on your application progress."
      actions={
        unreadCount > 0 ? (
          <span className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            {unreadCount} unread
          </span>
        ) : null
      }
    >
      <div className="rounded-lg border border-slate-200/90 bg-white shadow-sm overflow-hidden">
        {notificationsQuery.isLoading ? (
          <div className="divide-y divide-slate-100">
            <SkeletonNotification />
            <SkeletonNotification />
            <SkeletonNotification />
            <SkeletonNotification />
          </div>
        ) : notifications.length === 0 ? (
          <div className="py-16 text-center">
            <svg
              className="mx-auto h-12 w-12 text-slate-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
              />
            </svg>
            <p className="mt-4 text-base font-medium text-slate-700">No notifications yet</p>
            <p className="mt-1 text-sm text-slate-500">
              You&apos;ll receive updates here as your applications progress.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => (
              <button
                key={notification.id}
                onClick={() => handleClick(notification)}
                className={`w-full flex items-start gap-4 p-5 text-left transition hover:bg-slate-50 ${
                  !notification.is_read ? "bg-blue-50/40" : ""
                }`}
              >
                <NotificationIcon type={notification.type} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p
                      className={`text-sm font-medium ${
                        notification.is_read ? "text-slate-700" : "text-slate-900"
                      }`}
                    >
                      {notification.title}
                    </p>
                    {!notification.is_read && (
                      <span className="h-2 w-2 rounded-full bg-blue-600 shrink-0" />
                    )}
                  </div>
                  <p className="mt-0.5 text-sm text-slate-500 line-clamp-2">
                    {notification.message}
                  </p>
                </div>
                <span className="text-xs text-slate-400 shrink-0 whitespace-nowrap mt-0.5">
                  {formatTimeAgo(notification.created_at)}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {!notificationsQuery.isLoading && notifications.length > 0 && (
        <p className="mt-4 text-xs text-slate-400 text-right">
          {notifications.length} notification{notifications.length !== 1 ? "s" : ""}
          {unreadCount > 0 ? ` · ${unreadCount} unread` : ""}
        </p>
      )}
    </DashboardShell>
  );
}
