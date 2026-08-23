// Centralized API client for RevEngine AI backend
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RecoveryEvent {
  recovery_id: string;
  original_charge_id: string;
  customer_id: string | null;
  customer_email: string | null;
  customer_name: string | null;
  raw_error_code: string | null;
  failure_category: string;
  failure_description: string | null;
  amount: number | null;
  currency: string;
  customer_ltv: number;
  churn_risk_score: number;
  status: string;
  attribution_status: string;
  retry_schedule: RetrySlot[];
  touchpoint_count: number;
  settlement_amount: number | null;
  intervention_trail: InterventionItem[];
  created_at: string;
  updated_at: string;
}

export interface RetrySlot {
  scheduled_at: string;
  confidence_score: number;
  reason: string;
  window_label: string;
}

export interface InterventionItem {
  timestamp: string;
  channel: string;
  template_id: string;
  tone_confidence: number;
  message_preview: string;
  payer_response: string | null;
}

export interface DashboardSummary {
  total_events: number;
  total_recovered: number;
  total_amount_recovered: number;
  gross_recovery_rate: number;
  agent_driven_count: number;
  organic_count: number;
  holdout_count: number;
  net_agent_recovery: number;
  active_interventions: number;
  category_breakdown: Record<string, number>;
  recent_events: RecoveryEvent[];
}

export interface SimulateRequest {
  scenario: string;
  amount?: number;
  customer_name?: string;
  customer_email?: string;
}

export interface SimulateResult {
  scenario: string;
  recovery_id: string;
  charge_id: string;
  failure_category: string;
  status: string;
  attribution_status: string;
  retry_schedule: RetrySlot[];
  intervention_trail: InterventionItem[];
  customer_ltv: number;
  churn_risk_score: number;
}

export interface TrendPoint {
  date: string;
  total: number;
  recovered: number;
  rate: number;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  getDashboardSummary: () => apiFetch<DashboardSummary>("/dashboard/summary"),
  getEvents: (params?: { limit?: number; status?: string; category?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.status) qs.set("status", params.status);
    if (params?.category) qs.set("category", params.category);
    return apiFetch<RecoveryEvent[]>(`/dashboard/events?${qs}`);
  },
  getAttributionStats: () => apiFetch<Record<string, number>>("/dashboard/attribution-stats"),
  getRecoveryTrend: (days = 7) => apiFetch<TrendPoint[]>(`/dashboard/recovery-trend?days=${days}`),
  simulateEvent: (req: SimulateRequest) =>
    apiFetch<SimulateResult>("/simulate/fire", { method: "POST", body: JSON.stringify(req) }),
  simulateBulk: (count = 20) =>
    apiFetch<{ fired: number; events: SimulateResult[] }>(`/simulate/bulk?count=${count}`, { method: "POST" }),
  simulateRecovery: (recoveryId: string) =>
    apiFetch<{ status: string; settlement_amount: number; attribution_status: string }>(
      `/simulate/recover/${recoveryId}`,
      { method: "POST" }
    ),
  listScenarios: () =>
    apiFetch<{ key: string; description: string; error_code: string }[]>("/simulate/scenarios"),
};
