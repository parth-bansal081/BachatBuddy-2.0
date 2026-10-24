const API_BASE = import.meta.env.VITE_API_BASE_URL;

async function getAuthHeader(): Promise<string | null> {
  const { supabase } = await import("@/integrations/supabase/client");
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAuthHeader();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) message = body.detail;
    } catch {}
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface EnrichResult {
  narrations_seen: number;
  new_narrations: number;
  new_keys: number;
  llm_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  fallbacks: number;
  needs_review: number;
}

export interface CompileRequest {
  text: string;
}

export interface CompileResult {
  ok: boolean;
  policy: Policy | null;
  unsupported: string[];
  message: string | null;
  llm_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface Policy {
  name: string;
  rules: Rule[];
}

export type Rule =
  | { type: "save_percent"; percent: number; label: string }
  | { type: "category_cap"; category: string; monthly_limit: number }
  | { type: "bill_reserve"; name: string; amount: number; due_day: number };

export interface BacktestRequest {
  policy: Policy;
}

export interface BacktestResult {
  policy_name: string;
  first_day: string | null;
  last_day: string | null;
  months: MonthOut[];
  events: EventOut[];
  total_income: number;
  total_spend: number;
  total_reserved: number;
  cap_breaches: number;
  over_cap_total: number;
  headline: string;
  warnings: string[];
}

export interface MonthOut {
  month: string;
  income: number;
  saved: number;
  spend: number;
  reserved: number;
  left_after_policy: number;
  caps: CapOut[];
}

export interface CapOut {
  category: string;
  limit: number;
  spent: number;
  breached: boolean;
  over_by: number;
}

export interface EventOut {
  day: string;
  kind: "saved" | "cap_warning" | "cap_breached" | "bill_reserved";
  rule: string;
  amount: number;
  detail: string;
}

export interface SaveRequest {
  policy: Policy;
  source_text: string | null;
}

export interface SaveResponse {
  id: string;
}

export interface ActivePolicyResponse {
  policy: Policy | null;
  source_text: string | null;
}

export interface SafeToSpend {
  as_of: string;
  amount: number;
  income_used: number;
  saved: number;
  spent: number;
  reserved_upcoming: number;
  notes: string[];
}

export interface ActionOut {
  id: string;
  user_id: string;
  kind: string;
  label: string;
  amount: string;
  month: string;
  status: string;
  created_at: string;
  decided_at: string | null;
}

export interface GenerateResponse {
  month: string;
  actions: ActionOut[];
}

export interface ActionDecision {
  decision: "approved" | "rejected";
}

export const api = {
  enrich: () => apiFetch<EnrichResult>("/enrich", { method: "POST" }),
  compile: (text: string) =>
    apiFetch<CompileResult>("/policy/compile", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  backtest: (policy: Policy) =>
    apiFetch<BacktestResult>("/policy/backtest", {
      method: "POST",
      body: JSON.stringify({ policy }),
    }),
  save: (policy: Policy, source_text: string | null) =>
    apiFetch<SaveResponse>("/policy", {
      method: "POST",
      body: JSON.stringify({ policy, source_text }),
    }),
  active: () => apiFetch<ActivePolicyResponse>("/policy/active"),
  safeToSpend: () => apiFetch<SafeToSpend>("/policy/safe-to-spend"),
  actionsGenerate: () =>
    apiFetch<GenerateResponse>("/actions/generate", { method: "POST" }),
  actionsPending: () => apiFetch<ActionOut[]>("/actions/pending"),
  actionsDecide: (id: string, decision: "approved" | "rejected") =>
    apiFetch<ActionOut>(`/actions/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }),
};