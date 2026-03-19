import {
  EnrollmentRequest,
  EnrollmentSummary,
  ProcessedEnrollment,
} from "./types";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed with status ${res.status}`);
  }
  return res.json();
}

// Enrollment Service (proxied through Next.js rewrites)

export async function submitEnrollment(
  request: EnrollmentRequest
): Promise<EnrollmentSummary> {
  return fetchJson<EnrollmentSummary>("/api/enrollments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export async function getEnrollmentById(
  enrollmentId: string
): Promise<EnrollmentSummary> {
  return fetchJson<EnrollmentSummary>(
    `/api/enrollments/${encodeURIComponent(enrollmentId)}`
  );
}

export async function getEnrollmentByEmployee(
  employeeId: string
): Promise<EnrollmentSummary> {
  return fetchJson<EnrollmentSummary>(
    `/api/enrollments/by-employee/${encodeURIComponent(employeeId)}`
  );
}

export async function getEnrollmentByName(
  name: string
): Promise<EnrollmentSummary> {
  return fetchJson<EnrollmentSummary>(
    `/api/enrollments/by-name/${encodeURIComponent(name)}`
  );
}

export async function getEnrollmentsByStatus(
  status: string
): Promise<EnrollmentSummary[]> {
  return fetchJson<EnrollmentSummary[]>(
    `/api/enrollments/by-status?status=${encodeURIComponent(status)}`
  );
}

// Processing Service (proxied through Next.js rewrites)

export async function getProcessedEnrollmentById(
  enrollmentId: string
): Promise<ProcessedEnrollment> {
  return fetchJson<ProcessedEnrollment>(
    `/api/processed-enrollments/${encodeURIComponent(enrollmentId)}`
  );
}

export async function getProcessedEnrollmentByEmployee(
  employeeId: string
): Promise<ProcessedEnrollment> {
  return fetchJson<ProcessedEnrollment>(
    `/api/processed-enrollments/by-employee/${encodeURIComponent(employeeId)}`
  );
}

export async function getProcessedEnrollmentByName(
  name: string
): Promise<ProcessedEnrollment> {
  return fetchJson<ProcessedEnrollment>(
    `/api/processed-enrollments/by-name/${encodeURIComponent(name)}`
  );
}

// AI Gateway (proxied through Next.js rewrites)

export interface ChatResponse {
  conversation_id: string;
  message: string;
  tool_calls_made: string[];
  created_at: string;
}

export async function sendChatMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  return fetchJson<ChatResponse>("/api/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId || null,
    }),
  });
}

export async function checkAiHealth(): Promise<{ status: string }> {
  return fetchJson<{ status: string }>("/api/ai/health");
}
