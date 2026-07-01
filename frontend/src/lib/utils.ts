"use client";

/**
 * Patterns that indicate developer-facing messages that should be replaced.
 */
const API_PATTERNS: Array<{ pattern: RegExp; replacement: string }> = [
  { pattern: /POST\s+\/api\/v1\/jobs\/[^/]+\/match/i, replacement: "Please run AI Matching first." },
  { pattern: /GET\s+\/api/i, replacement: "Unable to load data. Please refresh and try again." },
  { pattern: /POST\s+\/api/i, replacement: "Action failed. Please try again." },
  { pattern: /PATCH\s+\/api/i, replacement: "Update failed. Please try again." },
  { pattern: /DELETE\s+\/api/i, replacement: "Deletion failed. Please try again." },
  { pattern: /no\s+matches?\s+found.*?match\s+first/i, replacement: "No candidate matches available. Please run AI Matching first." },
  { pattern: /no\s+rankings?\s+found.*?rank\s+first/i, replacement: "No rankings available. Please run AI Ranking first." },
  { pattern: /no\s+candidate.*?profile/i, replacement: "Candidate profile not found. Please complete your profile first." },
  { pattern: /no\s+resume/i, replacement: "No resume found. Please upload your resume first." },
  { pattern: /UUID|uuid|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, replacement: "" },
  { pattern: /\/api\/v1\/[^\s"')]+/gi, replacement: "" },
  { pattern: /sqlalchemy|database|postgres|sql|traceback|internal server/i, replacement: "An unexpected error occurred. Please try again." },
  { pattern: /KeyError|AttributeError|TypeError|ValueError|IndexError/i, replacement: "An unexpected error occurred. Please try again." },
];

/**
 * Sanitize a backend error message to be user-friendly.
 */
function sanitizeMessage(msg: string): string {
  let result = msg;
  for (const { pattern, replacement } of API_PATTERNS) {
    if (pattern.test(result)) {
      // If pattern matches and replacement is empty, clean the match inline
      if (replacement === "") {
        result = result.replace(pattern, "").trim();
      } else {
        return replacement;
      }
    }
  }
  // Clean up any remaining double spaces or orphaned punctuation
  result = result.replace(/\s{2,}/g, " ").replace(/^\s*[.,;:]\s*/, "").trim();
  return result || "An unexpected error occurred. Please try again.";
}

/**
 * Shared utility to extract a human-readable error message from API errors.
 * Sanitizes backend/developer terminology before returning to the user.
 */
export function getApiError(error: unknown, fallback: string): string {
  const e = error as {
    response?: { data?: { detail?: string | Array<{ msg: string }> }; status?: number };
    message?: string;
  };

  // Handle specific HTTP status codes first
  if (e?.response?.status === 429) return "Too many requests. Please wait a moment and try again.";
  if (e?.response?.status === 503) return "Service temporarily unavailable. Please try again shortly.";
  if (e?.response?.status === 500) {
    const detail = e?.response?.data?.detail;
    if (typeof detail === "string") return sanitizeMessage(detail);
    return "Something went wrong on our end. Please try again.";
  }
  if (e?.response?.status === 403) return "You don't have permission for this action.";
  if (e?.response?.status === 401) return "Your session has expired. Please log in again.";

  const detail = e?.response?.data?.detail;
  if (typeof detail === "string") return sanitizeMessage(detail);
  if (Array.isArray(detail) && detail.length > 0) {
    return sanitizeMessage(detail.map((d) => d.msg).join("; "));
  }
  if (e?.message && !e.message.includes("AxiosError")) return sanitizeMessage(e.message);
  return fallback;
}

/**
 * Validate a meeting link URL.
 * Accepts Google Meet, Zoom, and Microsoft Teams links.
 * Returns null if valid, or an error message if invalid.
 */
export function validateMeetingLink(url: string): string | null {
  if (!url || url.trim() === "") return null; // optional field

  const trimmed = url.trim();

  // Basic URL format check
  try {
    const parsed = new URL(trimmed);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      return "Meeting link must start with https://";
    }
  } catch {
    return "Please enter a valid URL (e.g., https://meet.google.com/...)";
  }

  // Check against allowed meeting platforms
  const allowedDomains = [
    /^meet\.google\.com$/i,
    /^([\w-]+\.)?zoom\.us$/i,
    /^teams\.microsoft\.com$/i,
    /^teams\.live\.com$/i,
  ];

  try {
    const { hostname } = new URL(trimmed);
    const isAllowed = allowedDomains.some((regex) => regex.test(hostname));
    if (!isAllowed) {
      return "Please use a Google Meet, Zoom, or Microsoft Teams link.";
    }
  } catch {
    return "Please enter a valid meeting URL.";
  }

  return null; // valid
}
