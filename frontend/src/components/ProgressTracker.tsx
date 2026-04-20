"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, AlertCircle, Loader2, Copy, Check } from "lucide-react";

import { fetchPollStatus } from "@/lib/api";
import { copyToClipboard } from "@/lib/utils";
import type { JobStatus, ProgressEvent } from "@/lib/types";

interface Props {
  jobId: string;
  onDone: (jobId: string) => void;
  onFailed: (jobId: string, message: string) => void;
}

const STATUS_LABEL: Record<JobStatus, string> = {
  queued: "Na fila",
  reading: "Lendo CSV",
  cleaning: "Higienizando dados",
  computing: "Calculando KPIs",
  persisting: "Persistindo no PostgreSQL",
  ai: "Gerando insights IA",
  embedding: "Indexando (RAG)",
  done: "Concluído",
  failed: "Falhou",
};

const POLL_INTERVAL_MS = 1000;

export function ProgressTracker({ jobId, onDone, onFailed }: Props) {
  const [event, setEvent] = useState<ProgressEvent | null>(null);
  const [copied, setCopied] = useState(false);
  const settled = useRef(false);

  const finish = useCallback(
    (status: "done" | "failed", message?: string) => {
      if (settled.current) return;
      settled.current = true;
      if (status === "done") onDone(jobId);
      else onFailed(jobId, message ?? "Erro desconhecido");
    },
    [jobId, onDone, onFailed],
  );

  useEffect(() => {
    settled.current = false;

    const poll = setInterval(async () => {
      if (settled.current) return;
      try {
        const data = await fetchPollStatus(jobId);
        setEvent(data);
        if (data.status === "done") finish("done");
        else if (data.status === "failed") finish("failed", data.message);
      } catch {
        // endpoint not ready or failed
      }
    }, POLL_INTERVAL_MS);

    return () => {
      clearInterval(poll);
    };
  }, [jobId, finish]);

  const status: JobStatus = event?.status ?? "queued";
  const progress = event?.progress ?? 0;
  const isDone = status === "done";
  const isFailed = status === "failed";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {isDone ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          ) : isFailed ? (
            <AlertCircle className="h-5 w-5 text-red-600" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-brand" />
          )}
          <div>
            <p className="text-sm font-medium">{STATUS_LABEL[status]}</p>
            <p className="text-xs text-slate-500 flex items-center gap-1.5">
              Job <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px]">{jobId}</code>
              <button
                onClick={async () => {
                  const ok = await copyToClipboard(jobId);
                  if (ok) {
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }
                }}
                className="p-1 hover:bg-slate-100 rounded-md transition-colors text-slate-400 hover:text-brand"
                title="Copiar ID do Job"
              >
                {copied ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
              </button>
            </p>
          </div>
        </div>
        <span className="text-sm font-semibold tabular-nums">{progress}%</span>
      </div>

      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full transition-all duration-300 ${isFailed ? "bg-red-500" : isDone ? "bg-emerald-500" : "bg-brand"
            }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {event?.message && (
        <p className="mt-3 text-sm text-slate-600">{event.message}</p>
      )}
    </div>
  );
}
