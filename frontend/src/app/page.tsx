"use client";

import { useCallback, useEffect, useState } from "react";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { UploadCard } from "@/components/UploadCard";
import { ProgressTracker } from "@/components/ProgressTracker";
import { Dashboard } from "@/components/Dashboard";
import { Chat } from "@/components/Chat";
import { TransactionsTable } from "@/components/TransactionsTable";
import { ResumeJobCard } from "@/components/ResumeJobCard";
import { fetchPollStatus } from "@/lib/api";
import type { JobCreatedResponse } from "@/lib/types";
import { Trash2 } from "lucide-react";

type Phase = "idle" | "loading" | "processing" | "ready" | "failed";

export default function HomePage() {
  const [job, setJob] = useState<JobCreatedResponse | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [failureMessage, setFailureMessage] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlJobId = params.get("jobId");

    const storageItem = localStorage.getItem("finance_last_job");
    let storedJobId = "";
    let storedFilename = "";
    if (storageItem) {
      try {
        const parsed = JSON.parse(storageItem);
        storedJobId = parsed.jobId;
        storedFilename = parsed.filename || "";
      } catch {
        storedJobId = storageItem;
      }
    }

    const targetJobId = urlJobId || storedJobId;
    if (!targetJobId) {
      setPhase("idle");
      return;
    }

    // Tenta recuperar via API de Status  detecção de existência e status
    fetchPollStatus(targetJobId).then((statusData) => {
      if (statusData && statusData.job_id) {
        const jobInfo: JobCreatedResponse = {
          job_id: statusData.job_id,
          status: statusData.status,
          filename: statusData.filename || storedFilename || "Arquivo"
        };
        setJob(jobInfo);

        // Se estiver pronto, exibe dashboard. Se não, exibe o progresso.
        setPhase(statusData.status === "done" ? "ready" : "processing");
      } else {
        setPhase("idle");
      }
    }).catch(() => {
      setPhase("idle");
    });
  }, []);

  const onJobCreated = useCallback((j: JobCreatedResponse) => {
    localStorage.setItem("finance_last_job", JSON.stringify({ jobId: j.job_id, filename: j.filename }));

    // Atualiza URL sem recarregar
    const url = new URL(window.location.href);
    url.searchParams.set("jobId", j.job_id);
    window.history.pushState({}, "", url);

    setJob(j);
    setPhase("processing");
    setFailureMessage(null);
  }, []);

  const onJobFound = useCallback((j: JobCreatedResponse) => {
    localStorage.setItem("finance_last_job", JSON.stringify({ jobId: j.job_id, filename: j.filename }));
    setJob(j);
    setPhase(j.status === "done" ? "ready" : "processing");
    setFailureMessage(null);

    const url = new URL(window.location.href);
    url.searchParams.set("jobId", j.job_id);
    window.history.pushState({}, "", url);
  }, []);

  const onReset = useCallback(() => {
    localStorage.removeItem("finance_last_job");
    const url = new URL(window.location.href);
    url.searchParams.delete("jobId");
    window.history.pushState({}, "", url.pathname);

    setJob(null);
    setPhase("idle");
    setFailureMessage(null);
  }, []);

  const onDone = useCallback(() => setPhase("ready"), []);
  const onFailed = useCallback((_id: string, msg: string) => {
    setPhase("failed");
    setFailureMessage(msg);
  }, []);

  return (
    <main className="min-h-screen pb-20">
      <header className="sticky top-0 z-50 border-b border-black/5 bg-white/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex flex-col justify-center">
            <h1 className="text-xl font-semibold tracking-tight text-[#1d1d1f]">
              Plataforma de Inteligência Financeira
            </h1>
            <span className="text-xs font-medium text-slate-400 mt-0.5">
              Sistema Desenvolvido por Lucas Roberto de Abreu Rogenski
            </span>
          </div>
          {job && job.job_id && (
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-black/5 px-3 py-1 font-medium text-xs text-[#1d1d1f]">
                {job.filename || "Arquivo"}
              </span>
              <button
                onClick={onReset}
                title="Excluir arquivo e resetar painel"
                className="flex items-center justify-center rounded-full p-1.5 text-slate-400 opacity-70 transition-all hover:bg-red-50 hover:text-red-500 hover:opacity-100"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </header>

      <section className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        {phase === "loading" && (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent" />
            <span className="ml-3 text-sm text-gray-500">Carregando...</span>
          </div>
        )}

        {phase !== "loading" && !job && (
          <div className="grid gap-6 md:grid-cols-2">
            <UploadCard onJobCreated={onJobCreated} disabled={phase === "processing"} />
            <ResumeJobCard onJobFound={onJobFound} disabled={phase === "processing"} />
          </div>
        )}

        {job && (phase === "processing" || phase === "ready") && (
          <ProgressTracker key={job.job_id} jobId={job.job_id} onDone={onDone} onFailed={onFailed} />
        )}

        {phase === "failed" && failureMessage && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 shadow-apple flex items-center justify-between">
            <div>
              <strong>Falha no processamento:</strong> {failureMessage}
            </div>
            <button
              onClick={onReset}
              className="px-3 py-1 bg-red-100 rounded-lg font-semibold hover:bg-red-200 transition-colors"
            >
              Tentar outro arquivo
            </button>
          </div>
        )}

        {job && phase === "ready" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <ErrorBoundary fallbackMessage="Erro ao carregar o dashboard.">
              <Dashboard key={`dash-${job.job_id}`} jobId={job.job_id} />
            </ErrorBoundary>
            <ErrorBoundary fallbackMessage="Erro ao carregar as transações.">
              <TransactionsTable key={`txn-${job.job_id}`} jobId={job.job_id} />
            </ErrorBoundary>
            <ErrorBoundary fallbackMessage="Erro ao carregar o chat.">
              <Chat key={`chat-${job.job_id}`} jobId={job.job_id} />
            </ErrorBoundary>
          </div>
        )}
      </section>
    </main>
  );
}
