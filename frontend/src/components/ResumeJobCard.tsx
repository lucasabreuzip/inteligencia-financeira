"use client";

import { useState } from "react";
import { Search, Loader2, ArrowRight } from "lucide-react";
import { fetchPollStatus } from "@/lib/api";
import type { JobCreatedResponse } from "@/lib/types";

interface ResumeJobCardProps {
  onJobFound: (job: JobCreatedResponse) => void;
  disabled?: boolean;
}

export function ResumeJobCard({ onJobFound, disabled }: ResumeJobCardProps) {
  const [jobId, setJobId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResume = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanId = jobId.trim();
    if (!cleanId) return;

    setLoading(true);
    setError(null);

    try {
      const status = await fetchPollStatus(cleanId);
      onJobFound({
        job_id: status.job_id,
        status: status.status,
        filename: status.filename || "Arquivo Recuperado",
      });
    } catch (err: any) {
      setError("ID não encontrado ou inválido.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl border border-black/5 bg-white/50 p-6 shadow-apple backdrop-blur-sm transition-all hover:bg-white/80">
      <div className="flex items-center gap-3 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
          <Search className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold text-[#1d1d1f]">Retomar Análise</h3>
          <p className="text-sm text-slate-500">Insira o ID do Job de um arquivo já processado</p>
        </div>
      </div>

      <form onSubmit={handleResume} className="relative">
        <input
          type="text"
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
          placeholder="Ex: c3dcf2760efc49a19d4b..."
          disabled={disabled || loading}
          className="w-full rounded-2xl border border-black/5 bg-white px-5 py-4 pr-12 text-sm shadow-sm transition-all focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/5 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || loading || !jobId.trim()}
          className="absolute right-2 top-2 flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white shadow-lg shadow-brand/20 transition-all hover:scale-105 hover:bg-brand-dark active:scale-95 disabled:scale-100 disabled:bg-slate-200 disabled:shadow-none"
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <ArrowRight className="h-5 w-5" />
          )}
        </button>
      </form>

      {error && (
        <p className="mt-3 text-xs font-medium text-red-500 animate-in fade-in slide-in-from-top-1">
          {error}
        </p>
      )}
    </div>
  );
}
