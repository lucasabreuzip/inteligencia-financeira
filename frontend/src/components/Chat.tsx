"use client";

import { useRef, useState, useEffect } from "react";
import { Send, Loader2, MessageSquare, FileText, ShieldCheck, ShieldAlert, Wrench } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { askChatStream, fetchChatHistory, formatBRL } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";

interface Props {
  jobId: string;
}

interface LiveTool {
  name: string;
  summary?: string | null;
  ok?: boolean;
  done: boolean;
}

interface Turn {
  question: string;
  response?: ChatResponse;
  error?: string;
  loading: boolean;
  streamingAnswer?: string;
  liveTools?: LiveTool[];
}

const SUGGESTIONS = [
  "Quantas transações existem na base por status?",
  "Qual a receita total por mês?",
  "Liste as 20 maiores transações pendentes.",
  "Top 5 clientes por receita paga.",
  "Quais itens são referentes a contratação?",
];

function createSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function Chat({ jobId }: Props) {
  // session_id persiste por job no browser para manter uma conversa isolada.
  const SESSION_KEY = `chat_session_${jobId}`;
  const [sessionId, setSessionId] = useState<string>("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [topK, setTopK] = useState(15);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem(SESSION_KEY)?.trim();
    const sid = stored || createSessionId();
    if (!stored) {
      window.localStorage.setItem(SESSION_KEY, sid);
    }
    setSessionId(sid);

    // Rehidrata transcricao do backend. 
    fetchChatHistory(jobId, sid)
      .then((hist) => {
        const restored: Turn[] = [];
        for (let i = 0; i < hist.messages.length; i++) {
          const m = hist.messages[i];
          if (m.role !== "user") continue;
          const next = hist.messages[i + 1];
          const answer = next && next.role === "assistant" ? next.content : "";
          restored.push({
            question: m.content,
            loading: false,
            response: answer
              ? {
                job_id: jobId,
                question: m.content,
                answer,
                sources: [],
                tools_used: [],
                grounding: { cited: [], verified: [], unverified: [], is_grounded: true },
              }
              : undefined,
          });
        }
        setTurns(restored);
      })
      .catch((e) => console.error("Failed to load chat history", e));
  }, [SESSION_KEY, jobId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [turns]);

  async function submit(question: string) {
    const trimmed = question.trim();
    if (!trimmed || !sessionId) return;
    setInput("");
    const idx = turns.length;

    setTurns((prev) => [
      ...prev,
      { question: trimmed, loading: true, streamingAnswer: "", liveTools: [] },
    ]);

    // Atualiza apenas o turn
    const patchTurn = (patch: Partial<Turn>) => {
      setTurns((prev) => {
        const next = [...prev];
        if (next[idx]) next[idx] = { ...next[idx], ...patch };
        return next;
      });
    };

    try {
      await askChatStream(jobId, sessionId, trimmed, topK, (event) => {
        if (event.type === "token") {
          setTurns((prev) => {
            const next = [...prev];
            const cur = next[idx];
            if (!cur) return prev;
            next[idx] = {
              ...cur,
              streamingAnswer: (cur.streamingAnswer ?? "") + event.delta,
            };
            return next;
          });
        } else if (event.type === "tool_start") {
          setTurns((prev) => {
            const next = [...prev];
            const cur = next[idx];
            if (!cur) return prev;
            next[idx] = {
              ...cur,
              liveTools: [
                ...(cur.liveTools ?? []),
                { name: event.name, done: false },
              ],
            };
            return next;
          });
        } else if (event.type === "tool_end") {
          setTurns((prev) => {
            const next = [...prev];
            const cur = next[idx];
            if (!cur) return prev;
            const live = [...(cur.liveTools ?? [])];

            for (let i = live.length - 1; i >= 0; i--) {
              if (live[i].name === event.name && !live[i].done) {
                live[i] = { ...live[i], done: true, ok: event.ok, summary: event.summary };
                break;
              }
            }
            next[idx] = { ...cur, liveTools: live };
            return next;
          });
        } else if (event.type === "done") {
          patchTurn({
            response: event.response,
            loading: false,
            streamingAnswer: undefined,
            liveTools: undefined,
          });
        } else if (event.type === "error") {
          patchTurn({
            loading: false,
            error: event.message,
            streamingAnswer: undefined,
            liveTools: undefined,
          });
        }
      });
    } catch (e) {
      patchTurn({
        loading: false,
        error: e instanceof Error ? e.message : "Erro desconhecido",
        streamingAnswer: undefined,
        liveTools: undefined,
      });
    }
  }

  return (
    <div className="flex h-[600px] flex-col overflow-hidden rounded-[28px] border border-black/5 bg-white/80 shadow-apple backdrop-blur-xl transition-all duration-300 hover:shadow-apple-hover">
      <div className="flex items-center justify-between gap-3 border-b border-black/5 bg-white/60 px-6 py-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-brand" />
          <h3 className="text-lg font-semibold tracking-tight text-[#1d1d1f]">Pergunte à sua base (RAG)</h3>
        </div>
        <label className="flex items-center gap-2 text-xs font-medium tracking-tight text-black/50">
          Top-K:
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="rounded-lg border border-black/5 bg-white px-2 py-1 text-xs shadow-sm focus:border-brand focus:outline-none"
          >
            {[5, 10, 15, 25, 40, 50].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-6 py-6 scrollbar-hide">
        {turns.length === 0 && (
          <div>
            <p className="text-sm font-medium tracking-tight text-black/60">
              Faça perguntas fundamentadas nas transações já indexadas. Exemplos:
            </p>
            <div className="mt-4 flex flex-wrap gap-2.5">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="rounded-full border border-black/5 bg-white px-4 py-1.5 text-[13px] font-medium tracking-tight text-black/70 shadow-sm transition-all hover:scale-[1.02] hover:bg-slate-50 active:scale-[0.98]"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {turns.map((t, i) => (
          <div key={i} className="space-y-2">
            <div className="flex justify-end">
              <div className="max-w-[85%] rounded-lg bg-brand px-3 py-2 text-sm text-white">
                {t.question}
              </div>
            </div>

            {t.loading && (
              <div className="space-y-2">
                {t.liveTools && t.liveTools.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 text-[11px]">
                    {t.liveTools.map((lt, k) => (
                      <span
                        key={k}
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${!lt.done
                            ? "bg-brand/10 text-brand"
                            : lt.ok
                              ? "bg-slate-100 text-slate-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        title={lt.summary ?? ""}
                      >
                        {!lt.done ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <Wrench className="h-3 w-3" />
                        )}
                        {lt.name}
                        {lt.done && lt.summary ? ` · ${lt.summary}` : ""}
                      </span>
                    ))}
                  </div>
                )}

                {t.streamingAnswer ? (
                  <div className="prose prose-sm prose-slate max-w-none rounded-lg bg-slate-50 p-4 text-slate-800 break-words leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {t.streamingAnswer}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <Loader2 className="h-4 w-4 animate-spin" /> Consultando base…
                  </div>
                )}
              </div>
            )}

            {t.error && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {t.error}
              </div>
            )}

            {t.response && (
              <div className="space-y-2">
                <div className="prose prose-sm prose-slate max-w-none rounded-lg bg-slate-50 p-4 text-slate-800 break-words leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {t.response.answer}
                  </ReactMarkdown>
                </div>

                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  {t.response.grounding &&
                    (t.response.grounding.cited.length > 0 ||
                      t.response.grounding.unverified.length > 0) && (
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${t.response.grounding.is_grounded
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-amber-50 text-amber-700"
                          }`}
                        title={
                          t.response.grounding.is_grounded
                            ? "Todos os IDs citados foram verificados nas ferramentas."
                            : `IDs sem lastro: ${t.response.grounding.unverified.join(", ")}`
                        }
                      >
                        {t.response.grounding.is_grounded ? (
                          <ShieldCheck className="h-3 w-3" />
                        ) : (
                          <ShieldAlert className="h-3 w-3" />
                        )}
                        {t.response.grounding.is_grounded
                          ? `${t.response.grounding.verified.length} ID(s) verificado(s)`
                          : `${t.response.grounding.unverified.length} não verificado(s)`}
                      </span>
                    )}

                  {t.response.tools_used?.map((tl, k) => (
                    <span
                      key={k}
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${tl.ok
                        ? "bg-slate-100 text-slate-700"
                        : "bg-red-50 text-red-700"
                        }`}
                      title={tl.summary ?? ""}
                    >
                      <Wrench className="h-3 w-3" />
                      {tl.name}
                      {tl.summary ? ` · ${tl.summary}` : ""}
                    </span>
                  ))}
                </div>

                {t.response.sources.length > 0 && (
                  <details className="rounded-md border border-slate-200 bg-white">
                    <summary className="cursor-pointer px-3 py-2 text-xs font-medium text-slate-600">
                      <FileText className="mr-1 inline h-3 w-3" />
                      {t.response.sources.length} fonte(s)
                    </summary>
                    <ul className="divide-y divide-slate-100 text-xs">
                      {t.response.sources.map((s) => (
                        <li key={s.id} className="px-3 py-2">
                          <div className="flex justify-between">
                            <span className="font-mono text-slate-700">{s.id}</span>
                            <span className="tabular-nums text-slate-600">
                              {formatBRL(s.valor)}
                            </span>
                          </div>
                          <div className="text-slate-500">
                            {s.data} · {s.cliente} · {s.status}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <form
        className="flex gap-2 border-t border-slate-200 px-5 py-3"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pergunte sobre os dados…"
          className="flex-1 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="inline-flex items-center gap-1 rounded-md bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
