"use client";

import { useEffect, useState } from "react";
import {
  Wallet,
  Receipt,
  AlertTriangle,
  Hash,
  Loader2,
} from "lucide-react";

import { fetchAdvancedInsights, fetchDashboard, formatBRL, formatPercent } from "@/lib/api";
import type { AdvancedMetrics, DashboardKPIs } from "@/lib/types";

import { KpiCard } from "./KpiCard";
import { RevenueChart } from "./RevenueChart";
import { InsightsPanel } from "./InsightsPanel";
import { AdvancedInsightsPanel } from "./AdvancedInsightsPanel";
import { ClientBehaviorChart } from "./ClientBehaviorChart";

interface Props {
  jobId: string;
}

export function Dashboard({ jobId }: Props) {
  const [data, setData] = useState<DashboardKPIs | null>(null);
  const [advanced, setAdvanced] = useState<AdvancedMetrics | null>(null);
  const [advancedFailed, setAdvancedFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setAdvanced(null);
    setAdvancedFailed(false);
    setError(null);

    const MAX_ATTEMPTS = 4;
    const attempt = (n: number) => {
      fetchDashboard(jobId)
        .then((d) => {
          if (!cancelled) setData(d);
        })
        .catch((e) => {
          if (cancelled) return;
          if (n < MAX_ATTEMPTS) {
            const delay = Math.min(400 * 2 ** (n - 1), 2000);
            setTimeout(() => attempt(n + 1), delay);
          } else {
            setError(e instanceof Error ? e.message : "Erro ao carregar dashboard.");
          }
        });
    };
    attempt(1);

    fetchAdvancedInsights(jobId)
      .then((r) => {
        if (!cancelled) setAdvanced(r.metrics);
      })
      .catch(() => {
        if (!cancelled) setAdvancedFailed(true);
      });

    return () => {
      cancelled = true;
    };
  }, [jobId]);

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center gap-2 text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Carregando dashboard…
      </div>
    );
  }

  const periodo =
    data.periodo_inicio && data.periodo_fim
      ? `${data.periodo_inicio} x ${data.periodo_fim}`
      : "—";

  const inadTone =
    data.taxa_inadimplencia >= 0.3
      ? "danger"
      : data.taxa_inadimplencia >= 0.1
        ? "warning"
        : "success";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Receita total (pago)"
          value={formatBRL(data.receita_total)}
          hint={periodo}
          icon={Wallet}
          tone="success"
        />
        <KpiCard
          title="Ticket médio"
          value={formatBRL(data.ticket_medio)}
          hint={`${data.total_transacoes} transações`}
          icon={Receipt}
        />
        <KpiCard
          title="Taxa de inadimplência"
          value={formatPercent(data.taxa_inadimplencia)}
          hint={formatBRL(data.inadimplencia_valor)}
          icon={AlertTriangle}
          tone={inadTone}
        />
        <KpiCard
          title="Total de transações"
          value={data.total_transacoes.toString()}
          hint="Incluindo pendentes"
          icon={Hash}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RevenueChart data={data.timeseries} />
        </div>
        <div>
          {data.insights ? (
            <InsightsPanel insights={data.insights} />
          ) : (
            <div className="rounded-[24px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl flex h-full items-center justify-center text-center">
              <span className="text-sm font-medium text-slate-500">
                A análise inteligente não está disponível no momento.
              </span>
            </div>
          )}
        </div>
      </div>

      {advanced?.comportamento_clientes && advanced.comportamento_clientes.length > 0 && (
        <ClientBehaviorChart data={advanced.comportamento_clientes} />
      )}

      <AdvancedInsightsPanel jobId={jobId} metrics={advancedFailed ? undefined : advanced} />
    </div>
  );
}
