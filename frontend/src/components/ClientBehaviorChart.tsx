"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Users } from "lucide-react";

import { formatBRL } from "@/lib/api";
import type { AdvancedMetrics } from "@/lib/types";

interface Props {
  data: NonNullable<AdvancedMetrics["comportamento_clientes"]>;
}

type Health = "otimo" | "bom" | "atencao" | "risco";

const HEALTH_META: Record<
  Health,
  { label: string; color: string; badge: string; text: string }
> = {
  otimo: {
    label: "Ótimo pagador",
    color: "#10b981",
    badge: "bg-emerald-100",
    text: "text-emerald-700",
  },
  bom: {
    label: "Bom pagador",
    color: "#6366f1",
    badge: "bg-indigo-100",
    text: "text-indigo-700",
  },
  atencao: {
    label: "Atenção",
    color: "#f59e0b",
    badge: "bg-amber-100",
    text: "text-amber-700",
  },
  risco: {
    label: "Em risco",
    color: "#ef4444",
    badge: "bg-red-100",
    text: "text-red-700",
  },
};

function classify(pontualidade: number): Health {
  if (pontualidade >= 0.9) return "otimo";
  if (pontualidade >= 0.7) return "bom";
  if (pontualidade >= 0.5) return "atencao";
  return "risco";
}

function compactBRL(value: number): string {
  if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `R$ ${(value / 1_000).toFixed(0)}k`;
  return `R$ ${value.toFixed(0)}`;
}

export function ClientBehaviorChart({ data }: Props) {
  const { rows, healthPresent, summary } = useMemo(() => {
    const sorted = [...data].sort((a, b) => b.receita_total - a.receita_total);
    const enriched = sorted.map((d) => ({
      ...d,
      health: classify(d.taxa_pontualidade),
    }));

    const healthPresent = new Set(enriched.map((e) => e.health));

    const totalReceita = enriched.reduce((s, e) => s + e.receita_total, 0);
    const totalPago = enriched.reduce((s, e) => s + e.receita_paga, 0);
    const totalAberto = enriched.reduce((s, e) => s + e.receita_em_aberto, 0);
    const melhor = [...enriched].sort(
      (a, b) => b.taxa_pontualidade - a.taxa_pontualidade,
    )[0];
    const pior = [...enriched].sort(
      (a, b) => a.taxa_pontualidade - b.taxa_pontualidade,
    )[0];
    const topShare = enriched[0]
      ? enriched[0].receita_total / (totalReceita || 1)
      : 0;

    return {
      rows: enriched,
      healthPresent,
      summary: {
        totalReceita,
        totalPago,
        totalAberto,
        melhor,
        pior,
        topCliente: enriched[0],
        topShare,
      },
    };
  }, [data]);

  if (rows.length === 0) {
    return (
      <div className="rounded-[24px] border border-black/5 bg-white/80 p-6 text-sm text-black/50 shadow-apple backdrop-blur-xl">
        Sem dados suficientes para analisar comportamento de clientes.
      </div>
    );
  }

  const chartHeight = Math.max(220, rows.length * 44 + 40);

  return (
    <div className="rounded-[24px] border border-black/5 bg-white/80 p-6 shadow-apple backdrop-blur-xl transition-all duration-300 hover:shadow-apple-hover">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-brand" />
            <h3 className="text-xl font-semibold tracking-tight text-[#1d1d1f]">
              Comportamento de clientes
            </h3>
          </div>
          <p className="mt-1 text-xs font-medium tracking-tight text-black/50">
            Top {rows.length} por volume total
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-medium tracking-tight text-black/50">
          {(Object.keys(HEALTH_META) as Health[]).map((k) =>
            !healthPresent.has(k) ? null : (
              <span key={k} className="inline-flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: HEALTH_META[k].color }}
                />
                {HEALTH_META[k].label}
              </span>
            ),
          )}
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-sm">
          <p className="text-[11px] font-medium uppercase tracking-wide text-black/40">
            Maior cliente
          </p>
          <p className="mt-1 truncate text-sm font-semibold tracking-tight text-[#1d1d1f]">
            {summary.topCliente?.cliente ?? "—"}
          </p>
          <p className="text-[11px] font-medium tracking-tight text-black/50">
            {(summary.topShare * 100).toFixed(1)}% da receita
          </p>
        </div>
        <div className="rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-sm">
          <p className="text-[11px] font-medium uppercase tracking-wide text-black/40">
            Melhor pagador
          </p>
          <p className="mt-1 truncate text-sm font-semibold tracking-tight text-emerald-700">
            {summary.melhor?.cliente ?? "—"}
          </p>
          <p className="text-[11px] font-medium tracking-tight text-black/50 tabular-nums">
            {((summary.melhor?.taxa_pontualidade ?? 0) * 100).toFixed(0)}%
            pontualidade
          </p>
        </div>
        <div className="rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-sm">
          <p className="text-[11px] font-medium uppercase tracking-wide text-black/40">
            Requer atenção
          </p>
          <p className="mt-1 truncate text-sm font-semibold tracking-tight text-red-700">
            {summary.pior?.cliente ?? "—"}
          </p>
          <p className="text-[11px] font-medium tracking-tight text-black/50 tabular-nums">
            {((summary.pior?.taxa_pontualidade ?? 0) * 100).toFixed(0)}%
            pontualidade
          </p>
        </div>
        <div className="rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-sm">
          <p className="text-[11px] font-medium uppercase tracking-wide text-black/40">
            Volume total
          </p>
          <p className="mt-1 text-sm font-semibold tracking-tight text-[#1d1d1f] tabular-nums">
            {compactBRL(summary.totalReceita)}
          </p>
          <p className="text-[11px] font-medium tracking-tight text-black/50 tabular-nums">
            {compactBRL(summary.totalPago)} pago ·{" "}
            <span className="text-amber-700">
              {compactBRL(summary.totalAberto)} em aberto
            </span>
          </p>
        </div>
      </div>

      <div style={{ height: chartHeight, minWidth: 0, minHeight: 0 }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ top: 4, right: 80, left: 8, bottom: 4 }}
            barCategoryGap={12}
          >
            <XAxis
              type="number"
              hide
              domain={[0, (dataMax: number) => dataMax * 1.08]}
            />
            <YAxis
              type="category"
              dataKey="cliente"
              stroke="#1d1d1f"
              fontSize={13}
              fontWeight={600}
              tickLine={false}
              axisLine={false}
              width={130}
              tick={{ fill: "#1d1d1f" }}
            />
            <Tooltip
              cursor={{ fill: "rgba(0,0,0,0.04)" }}
              wrapperStyle={{ zIndex: 50, outline: "none" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as (typeof rows)[number];
                const meta = HEALTH_META[p.health];
                return (
                  <div
                    className="space-y-1.5 rounded-2xl border border-black/5 bg-white px-4 py-3 shadow-xl"
                    style={{ boxShadow: "0 12px 40px rgba(0,0,0,0.15)" }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ background: meta.color }}
                      />
                      <span className="text-[13px] font-semibold tracking-tight text-[#1d1d1f]">
                        {p.cliente}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-tight ${meta.badge} ${meta.text}`}
                      >
                        {meta.label}
                      </span>
                    </div>
                    <div className="space-y-0.5 text-[11px] tabular-nums text-black/60">
                      <div>
                        Volume total:{" "}
                        <span className="font-semibold text-brand">
                          {formatBRL(p.receita_total)}
                        </span>
                      </div>
                      <div>
                        Pago:{" "}
                        <span className="font-semibold text-emerald-700">
                          {formatBRL(p.receita_paga)}
                        </span>
                      </div>
                      <div>
                        Em aberto:{" "}
                        <span className="font-semibold text-amber-700">
                          {formatBRL(p.receita_em_aberto)}
                        </span>
                      </div>
                      <div>
                        Transações:{" "}
                        <span className="font-semibold text-[#1d1d1f]">
                          {p.qtd_transacoes}
                        </span>{" "}
                        · ticket {formatBRL(p.ticket_medio)}
                      </div>
                      <div>
                        Pontualidade:{" "}
                        <span className={`font-semibold ${meta.text}`}>
                          {(p.taxa_pontualidade * 100).toFixed(0)}%
                        </span>
                        {" · "}
                        última há{" "}
                        <span className="font-semibold text-[#1d1d1f]">
                          {p.recencia_dias}d
                        </span>
                      </div>
                    </div>
                  </div>
                );
              }}
            />
            <Bar dataKey="receita_paga" stackId="vol" radius={[6, 0, 0, 6]}>
              {rows.map((r) => (
                <Cell
                  key={`paga-${r.cliente}`}
                  fill={HEALTH_META[r.health].color}
                />
              ))}
            </Bar>
            <Bar
              dataKey="receita_em_aberto"
              stackId="vol"
              radius={[0, 6, 6, 0]}
            >
              {rows.map((r) => (
                <Cell
                  key={`aberto-${r.cliente}`}
                  fill={HEALTH_META[r.health].color}
                  fillOpacity={0.22}
                />
              ))}
              <LabelList
                dataKey="receita_total"
                position="right"
                offset={8}
                formatter={(value) => compactBRL(Number(value))}
                style={{ fill: "#1d1d1f", fontSize: 12, fontWeight: 600 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 border-t border-black/5 pt-4 text-[12px] md:grid-cols-2">
        {rows.map((r) => {
          const meta = HEALTH_META[r.health];
          return (
            <div
              key={r.cliente}
              className="flex items-center justify-between gap-3 rounded-xl bg-white/60 px-3 py-2"
            >
              <div className="flex min-w-0 items-center gap-2">
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ background: meta.color }}
                />
                <span className="truncate font-semibold tracking-tight text-[#1d1d1f]">
                  {r.cliente}
                </span>
              </div>
              <div className="flex shrink-0 items-center gap-3 text-[11px] tabular-nums text-black/55">
                <span>
                  {r.qtd_transacoes} txns ·{" "}
                  <span className="text-amber-700">
                    {compactBRL(r.receita_em_aberto)} aberto
                  </span>
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 font-semibold ${meta.badge} ${meta.text}`}
                >
                  {(r.taxa_pontualidade * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
