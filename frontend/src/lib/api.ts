import { AuditResult, GrievanceResponse } from "@/types";

/**
 * Resolves the backend URL dynamically:
 * - Server-side (Vercel functions/SSR): Uses process.env.BACKEND_URL injected by Vercel service binding
 * - Client-side (Browser on Vercel): Uses relative path "" (same domain via top-level rewrites)
 * - Standalone local dev: Uses process.env.NEXT_PUBLIC_API_URL or http://localhost:8000
 */
function getBackendUrl(path: string): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  // Server-side execution in Vercel functions / Server Components
  if (typeof window === "undefined" && process.env.BACKEND_URL) {
    const base = process.env.BACKEND_URL.replace(/\/$/, "");
    return `${base}${cleanPath}`;
  }

  // Client-side in browser or standalone local dev
  const publicBase = process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "";
  return `${publicBase}${cleanPath}`;
}

export async function uploadBill(formData: FormData): Promise<{ audit_id: string; status: string; message: string }> {
  const url = getBackendUrl("/api/v1/audit/upload");
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Upload failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getAuditResult(auditId: string): Promise<AuditResult> {
  const url = getBackendUrl(`/api/v1/audit/${auditId}`);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch audit result: ${res.statusText}`);
  }
  return res.json();
}

export async function startGrievance(auditId: string): Promise<GrievanceResponse> {
  const url = getBackendUrl("/api/v1/grievance/start");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audit_id: auditId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to initiate CGRMS session: ${res.statusText}`);
  }
  return res.json();
}

export async function submitOtp(threadId: string, otp: string): Promise<{ status: string; message: string }> {
  const url = getBackendUrl("/api/v1/grievance/otp");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, otp }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `OTP verification failed: ${res.statusText}`);
  }
  return res.json();
}

export function getReportDownloadUrl(auditId: string): string {
  return getBackendUrl(`/api/v1/audit/${auditId}/report`);
}

export function getVoiceUrl(auditId: string, language: string = "hi"): string {
  return getBackendUrl(`/api/v1/audit/${auditId}/voice?lang=${language}`);
}

export function getWebSocketUrl(auditId: string): string {
  if (typeof window !== "undefined") {
    if (process.env.NEXT_PUBLIC_API_URL) {
      return `${process.env.NEXT_PUBLIC_API_URL.replace(/^http/, "ws")}/ws/audit/${auditId}`;
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/audit/${auditId}`;
  }
  const base = process.env.BACKEND_URL || "http://localhost:8000";
  return `${base.replace(/^http/, "ws")}/ws/audit/${auditId}`;
}

export function getBrowserStreamUrl(threadId: string): string {
  if (typeof window !== "undefined") {
    if (process.env.NEXT_PUBLIC_API_URL) {
      return `${process.env.NEXT_PUBLIC_API_URL.replace(/^http/, "ws")}/ws/browser/${threadId}`;
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/browser/${threadId}`;
  }
  const base = process.env.BACKEND_URL || "http://localhost:8000";
  return `${base.replace(/^http/, "ws")}/ws/browser/${threadId}`;
}
