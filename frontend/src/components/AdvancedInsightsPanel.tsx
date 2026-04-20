"use client";

import { useEffect, useState } from "react";
import { Activity, Loader2 } from "lucide-react";

import { fetchAdvancedInsights, formatBRL } from "@/lib/api";
import type { AdvancedMetrics } from "@/lib/types";

import { CashflowBarChart } from "./CashflowBarChart";

interface Props {
  jobId: string;
  metrics?: AdvancedMetrics | null;
}

function pct(v: number | undefined, digits = 1): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

function signed(v: number | undefined): string {
  if (v == null) return "—";
  const p = (v * 100).toFixed(1);
  return v >= 0 ? `+${p}%` : `${p}%`;
}

function SectionCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof Activity;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[20px] border border-black/5 bg-white/80 p-5 shadow-apple backdrop-blur-xl">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-brand" />
        <h4 className="text-sm font-semibold tracking-tight text-[#1d1d1f]">{title}</h4>
      </div>
      {children}
    </div>
  );
}

function StatBlock({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "good" | "bad" | "warn";
}) {
  const toneClass =
    tone === "good"
      ? "text-emerald-700"
      : tone === "bad"
        ? "text-red-700"
        : tone === "warn"
          ? "text-amber-700"
          : "text-[#1d1d1f]";
  return (
    <div className="rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-sm">
      <p className="text-[11px] font-medium uppercase tracking-wide text-black/40">{label}</p>
      <p className={`mt-1 text-lg font-semibold tracking-tight tabular-nums ${toneClass}`}>{value}</p>
    </div>
  );
}

export function AdvancedInsightsPanel({ jobId, metrics }: Props) {
  const [data, setData] = useState<AdvancedMetrics | null>(metrics ?? null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (metrics !== undefined) {
      setData(metrics);
      return;
    }
    let cancel = false;
    setData(null);
    setError(null);
    fetchAdvancedInsights(jobId)
      .then((r) => {
        if (!cancel) setData(r.metrics);
      })
      .catch((e) => {
        if (!cancel) setError(e instanceof Error ? e.message : "Erro ao carregar insights avançados.");
      });
    return () => {
      cancel = true;
    };
  }, [jobId, metrics]);

  if (error) {
    return (
      <div className="rounded-[20px] border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center gap-2 rounded-[20px] border border-black/5 bg-white/80 p-5 text-sm text-black/50 shadow-apple">
        <Loader2 className="h-4 w-4 animate-spin" /> Calculando análises avançadas…
      </div>
    );
  }

  const fluxo = data.fluxo_caixa;
  const ultVar = fluxo.variacao_ultimo_mes;
  const ultTone = ultVar == null ? "neutral" : ultVar > 0.05 ? "good" : ultVar < -0.1 ? "bad" : "warn";

  return (
    <div className="space-y-4">
      <div className="rounded-[20px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold tracking-tight text-[#1d1d1f]">
              Fluxo de caixa · Variação M/M
            </h4>
            <span className="rounded-full bg-black/5 px-2 py-0.5 text-[10px] font-semibold tracking-tight text-black/60">
              {fluxo.meses_analisados} meses
            </span>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-medium tracking-tight text-black/40">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-sm bg-emerald-500" /> Alta
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-sm bg-red-500" /> Queda
            </span>
          </div>
        </div>

        <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatBlock label="Δ médio M/M" value={signed(fluxo.variacao_media_mm)} />
          <StatBlock label="Último mês" value={signed(ultVar)} tone={ultTone} />
          <StatBlock label="Aceleração" value={signed(fluxo.aceleracao_ultimo_mes)} />
          {fluxo.receita_ultimo_mes != null && (
            <StatBlock
              label="Receita último"
              value={formatBRL(fluxo.receita_ultimo_mes)}
            />
          )}
        </div>

        <CashflowBarChart data={fluxo.serie_mensal ?? []} height={200} />

        {(fluxo.maior_queda_mm || fluxo.maior_alta_mm) && (
          <div className="mt-4 flex flex-wrap gap-2 border-t border-black/5 pt-4 text-[12px]">
            {fluxo.maior_queda_mm && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 font-medium text-red-700">
                Pior mês: {fluxo.maior_queda_mm.mes}
                <span className="tabular-nums">{signed(fluxo.maior_queda_mm.variacao)}</span>
              </span>
            )}
            {fluxo.maior_alta_mm && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 font-medium text-emerald-700">
                Melhor mês: {fluxo.maior_alta_mm.mes}
                <span className="tabular-nums">+{(fluxo.maior_alta_mm.variacao * 100).toFixed(1)}%</span>
              </span>
            )}
          </div>
        )}
      </div>

      {data.inadimplencia_por_categoria.length > 0 && (
        <SectionCard title="Inadimplência por categoria" icon={Activity}>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {data.inadimplencia_por_categoria.map((c) => (
              <div key={c.categoria} className="flex items-center justify-between text-[13px]">
                <span className="capitalize text-black/60">{c.categoria.replace(/_/g, " ")}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs tabular-nums text-black/50">{formatBRL(c.inad)}</span>
                  <span
                    className={`min-w-[52px] rounded-full px-2 py-0.5 text-center text-xs font-semibold tabular-nums ${c.taxa_inad > 0.3
                      ? "bg-red-100 text-red-700"
                      : c.taxa_inad > 0.15
                        ? "bg-amber-100 text-amber-700"
                        : "bg-emerald-100 text-emerald-700"
                      }`}
                  >
                    {pct(c.taxa_inad)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
