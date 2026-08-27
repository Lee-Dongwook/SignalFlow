const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export type DLQEventSummary = {
  event_id: string;
  error_message: string;
  reason: string;
  confidence: number;
  validation_status: string;
  approval_status: string;
};

type RecoveryChange = {
  field: string;
  before: unknown;
  after: unknown;
  reason: string;
};

export type DLQEventDetail = {
  event_id: string;
  error_message: string;
  reason: string;
  confidence: number;
  approval_status: string;
  raw_payload: unknown;
  changes: RecoveryChange[];
  corrected_payload: unknown | null;
  validation_result: { status: string; errors: string[] };
  audit_logs: string[];
  reprocess_result?: { status: string; target: string };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || "API request failed");
  }
  return response.json() as Promise<T>;
}

export function getDLQEvents() {
  return request<DLQEventSummary[]>("/api/v1/dlq/events");
}

export function getDLQEvent(eventId: string) {
  return request<DLQEventDetail>(`/api/v1/dlq/events/${eventId}`);
}

export function decideDLQEvent(eventId: string, decision: "approve" | "hold") {
  return request<DLQEventDetail>(`/api/v1/dlq/events/${eventId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}

export function reprocessDLQEvent(eventId: string) {
  return request<DLQEventDetail>(`/api/v1/dlq/events/${eventId}/reprocess`, {
    method: "POST",
  });
}

export function analyzeDLQEvent(eventId: string) {
  return request<DLQEventDetail>(`/api/v1/dlq/events/${eventId}/analyze`, {
    method: "POST",
  });
}
