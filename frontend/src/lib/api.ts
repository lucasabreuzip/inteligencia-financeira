import { parseSseStream } from "./sse";
import type {
  AdvancedInsightsResponse,
  ChatHistoryResponse,
  ChatResponse,
  DashboardKPIs,
  JobCreatedResponse,
  TransactionFilters,
  TransactionsPage,
} from "./types";

const BASE = "/api";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch { }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function uploadCsv(file: File): Promise<JobCreatedResponse> {
  const form = new FormData();
  form.append("file", file);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000);
  try {
    const res = await fetch(`${BASE}/upload`, {
      method: "POST",
      body: form,
      signal: controller.signal,
    });
    return await handle<JobCreatedResponse>(res);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Upload demorou demais. Verifique se o backend esta rodando.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchDashboard(jobId: string): Promise<DashboardKPIs> {
  const res = await fetch(`${BASE}/dashboard/${jobId}`, {
    cache: "no-store",
  });
  return handle<DashboardKPIs>(res);
}



export async function askChat(
  jobId: string,
  sessionId: string,
  question: string,
  topK = 5,
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, session_id: sessionId, question, top_k: topK }),
  });
  return handle<ChatResponse>(res);
}

export async function fetchChatHistory(
  jobId: string,
  sessionId: string,
): Promise<ChatHistoryResponse> {
  const res = await fetch(`${BASE}/chat/history/${jobId}/${sessionId}`, {
    cache: "no-store",
  });
  return handle<ChatHistoryResponse>(res);
}

export type ChatStreamEvent =
  | { type: "token"; delta: string }
  | { type: "tool_start"; name: string; args: Record<string, unknown>; call_id: string }
  | { type: "tool_end"; name: string; ok: boolean; summary: string | null; call_id: string }
  | { type: "done"; response: ChatResponse }
  | { type: "error"; message: string };

export async function askChatStream(
  jobId: string,
  sessionId: string,
  question: string,
  topK: number,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, session_id: sessionId, question, top_k: topK }),
    signal,
  });
  await parseSseStream<ChatStreamEvent>(res, onEvent);
}

export async function fetchPollStatus(jobId: string): Promise<any> {
  const res = await fetch(`${BASE}/status/${jobId}/poll`, {
    cache: "no-store",
  });
  return handle<any>(res);
}

export async function fetchAdvancedInsights(
  jobId: string,
): Promise<AdvancedInsightsResponse> {
  const res = await fetch(`${BASE}/insights/advanced/${jobId}?_=${Date.now()}`, {
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
  });
  return handle<AdvancedInsightsResponse>(res);
}

export async function listTransactions(
  jobId: string,
  filters: TransactionFilters,
): Promise<TransactionsPage> {
  const qs = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  const url = `${BASE}/transactions/${jobId}${qs.toString() ? `?${qs}` : ""}`;
  const res = await fetch(url, { cache: "no-store" });
  return handle<TransactionsPage>(res);
}

export function formatBRL(value: number): string {
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}
