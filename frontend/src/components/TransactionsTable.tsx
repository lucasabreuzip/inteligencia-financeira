"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Filter, ChevronLeft, ChevronRight } from "lucide-react";

import { formatBRL, listTransactions } from "@/lib/api";
import type { TransactionFilters, TransactionsPage } from "@/lib/types";

interface Props {
  jobId: string;
}

const STATUS_OPTS = ["", "pago", "pendente", "atrasado", "cancelado"];
const PAGE_SIZE = 15;

export function TransactionsTable({ jobId }: Props) {
  const [data, setData] = useState<TransactionsPage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<TransactionFilters>({
    limit: PAGE_SIZE,
    offset: 0,
    order_by: "data",
    order_dir: "desc",
  });

  useEffect(() => {
    let cancel = false;
    setLoading(true);
    setError(null);
    listTransactions(jobId, filters)
      .then((d) => {
        if (!cancel) setData(d);
      })
      .catch((e) => {
        if (!cancel) setError(e instanceof Error ? e.message : "Erro ao carregar");
      })
      .finally(() => {
        if (!cancel) setLoading(false);
      });
    return () => {
      cancel = true;
    };
  }, [jobId, filters]);

  const categorias = useMemo(
    () => (data?.categorias_disponiveis ? Object.entries(data.categorias_disponiveis) : []),
    [data],
  );

  const page = Math.floor((filters.offset ?? 0) / (filters.limit ?? PAGE_SIZE)) + 1;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / (filters.limit ?? PAGE_SIZE))) : 1;

  function patch(p: Partial<TransactionFilters>) {
    setFilters((prev) => ({ ...prev, offset: 0, ...p }));
  }

  return (
    <div className="overflow-hidden rounded-[24px] border border-black/5 bg-white/80 shadow-apple backdrop-blur-xl transition-all duration-300 hover:shadow-apple-hover">
      <div className="flex items-center gap-3 border-b border-black/5 bg-white/60 px-6 py-4">
        <Filter className="h-5 w-5 text-brand" />
        <h3 className="text-xl font-semibold tracking-tight text-[#1d1d1f]">Transações</h3>
        {data && (
          <span className="ml-auto text-xs font-semibold tracking-tight text-black/50 tabular-nums">
            {data.total} total · página {page}/{totalPages}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 border-b border-black/5 bg-white/40 px-6 py-5 md:grid-cols-6">
        <select
          value={filters.status ?? ""}
          onChange={(e) => patch({ status: e.target.value || undefined })}
          className="rounded-lg border border-black/5 bg-white px-2 py-1.5 text-[13px] font-medium tracking-tight text-black/70 shadow-sm focus:border-brand focus:outline-none"
        >
          {STATUS_OPTS.map((s) => (
            <option key={s} value={s}>
              {s ? s : "status: todos"}
            </option>
          ))}
        </select>

        <select
          value={filters.categoria ?? ""}
          onChange={(e) => patch({ categoria: e.target.value || undefined })}
          className="rounded-lg border border-black/5 bg-white px-2 py-1.5 text-[13px] font-medium tracking-tight text-black/70 shadow-sm focus:border-brand focus:outline-none"
        >
          <option value="">categoria: todas</option>
          {categorias.map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>

        <input
          type="text"
          value={filters.cliente_contains ?? ""}
          placeholder="cliente contém…"
          onChange={(e) => patch({ cliente_contains: e.target.value || undefined })}
          className="rounded-lg border border-black/5 bg-white px-3 py-1.5 text-[13px] font-medium tracking-tight text-black/70 shadow-sm focus:border-brand focus:outline-none placeholder:text-black/30"
        />

        <input
          type="number"
          value={filters.min_valor ?? ""}
          placeholder="valor min"
          onChange={(e) =>
            patch({ min_valor: e.target.value ? Number(e.target.value) : undefined })
          }
          className="rounded-lg border border-black/5 bg-white px-3 py-1.5 text-[13px] font-medium tracking-tight text-black/70 shadow-sm focus:border-brand focus:outline-none placeholder:text-black/30"
        />

        <input
          type="date"
          value={filters.data_inicio ?? ""}
          onChange={(e) => patch({ data_inicio: e.target.value || undefined })}
          className="rounded-lg border border-black/5 bg-white px-3 py-1.5 text-[13px] font-medium tracking-tight text-black/70 shadow-sm focus:border-brand focus:outline-none text-black/70"
        />
        <input
          type="date"
          value={filters.data_fim ?? ""}
          onChange={(e) => patch({ data_fim: e.target.value || undefined })}
          className="rounded border border-slate-200 bg-white px-2 py-1 text-xs"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              {(
                [
                  ["data", "Data"],
                  ["valor", "Valor"],
                  ["status", "Status"],
                  ["cliente", "Cliente"],
                ] as const
              ).map(([key, label]) => (
                <th
                  key={key}
                  className="cursor-pointer select-none px-4 py-2 text-left"
                  onClick={() =>
                    setFilters((prev) => ({
                      ...prev,
                      order_by: key,
                      order_dir:
                        prev.order_by === key && prev.order_dir === "desc" ? "asc" : "desc",
                    }))
                  }
                >
                  {label}
                  {filters.order_by === key && (
                    <span className="ml-1">{filters.order_dir === "asc" ? "↑" : "↓"}</span>
                  )}
                </th>
              ))}
              <th className="px-4 py-2 text-left">Categoria</th>
              <th className="px-4 py-2 text-left">Descrição</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading &&
              Array.from({ length: 10 }).map((_, i) => (
                <tr key={`skeleton-${i}`} className="animate-pulse border-b border-black/5">
                  <td className="px-4 py-3">
                    <div className="h-4 w-20 rounded-full bg-black/5" />
                  </td>
                  <td className="px-4 py-3">
                    <div className="h-4 w-24 rounded-full bg-black/5" />
                  </td>
                  <td className="px-4 py-3">
                    <div className="h-6 w-16 rounded-full bg-black/5" />
                  </td>
                  <td className="px-4 py-3">
                    <div className="h-4 w-32 rounded-full bg-black/5" />
                  </td>
                  <td className="px-4 py-3">
                    <div className="h-4 w-24 rounded-full bg-black/5" />
                  </td>
                  <td className="px-4 py-3">
                    <div className="h-4 w-64 rounded-full bg-black/5" />
                  </td>
                </tr>
              ))}
            {!loading && data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                  Nenhuma transação encontrada.
                </td>
              </tr>
            )}
            {!loading &&
              data?.items.map((t) => (
                <tr key={t.id} className="hover:bg-slate-50">
                  <td className="px-4 py-2 tabular-nums">{t.data}</td>
                  <td className="px-4 py-2 tabular-nums">{formatBRL(t.valor)}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        t.status === "pago"
                          ? "bg-emerald-100 text-emerald-700"
                          : t.status === "atrasado"
                          ? "bg-red-100 text-red-700"
                          : t.status === "cancelado"
                          ? "bg-slate-100 text-slate-600"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td className="px-4 py-2">{t.cliente}</td>
                  <td className="px-4 py-2 text-xs text-slate-600">
                    {data?.categorias_disponiveis[t.categoria] ?? t.categoria}
                  </td>
                  <td className="max-w-md truncate px-4 py-2 text-xs text-slate-600" title={t.descricao}>
                    {t.descricao}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {error && (
        <div className="border-t border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-slate-200 px-5 py-3">
        <button
          type="button"
          onClick={() =>
            setFilters((p) => ({
              ...p,
              offset: Math.max(0, (p.offset ?? 0) - (p.limit ?? PAGE_SIZE)),
            }))
          }
          disabled={!data || (filters.offset ?? 0) === 0}
          className="inline-flex items-center gap-1 rounded border border-slate-200 px-3 py-1 text-xs disabled:opacity-40"
        >
          <ChevronLeft className="h-3 w-3" /> Anterior
        </button>
        <span className="text-xs text-slate-500 font-medium">
          {data?.items.length ?? 0} exibidas · Página {page} de {totalPages}
        </span>
        <button
          type="button"
          onClick={() =>
            setFilters((p) => ({
              ...p,
              offset: (p.offset ?? 0) + (p.limit ?? PAGE_SIZE),
            }))
          }
          disabled={
            !data ||
            (filters.offset ?? 0) + (filters.limit ?? PAGE_SIZE) >= (data?.total ?? 0)
          }
          className="inline-flex items-center gap-1 rounded border border-slate-200 px-3 py-1 text-xs disabled:opacity-40"
        >
          Próxima <ChevronRight className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
