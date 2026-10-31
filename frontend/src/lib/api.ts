import { AuditResult, GrievanceResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadBill(formData: FormData): Promise<{ audit_id: string; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/audit/upload`, {
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
  const res = await fetch(`${API_BASE}/api/v1/audit/${auditId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch audit result: ${res.statusText}`);
  }
  return res.json();
}

export async function startGrievance(auditId: string): Promise<GrievanceResponse> {
  const res = await fetch(`${API_BASE}/api/v1/grievance/start`, {
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
  const res = await fetch(`${API_BASE}/api/v1/grievance/otp`, {
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
  return `${API_BASE}/api/v1/audit/${auditId}/report`;
}

export function getVoiceUrl(auditId: string, language: string = "hi"): string {
  return `${API_BASE}/api/v1/audit/${auditId}/voice?lang=${language}`;
}

export function getWebSocketUrl(auditId: string): string {
  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/ws/audit/${auditId}`;
}

export function getBrowserStreamUrl(threadId: string): string {
  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/ws/browser/${threadId}`;
}

