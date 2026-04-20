from __future__ import annotations

import pandas as pd

from app.core.constants import INADIMPLENCIA_STATUSES
from app.services.advanced_metrics import build_advanced_metrics


def compute_kpis(df: pd.DataFrame) -> dict:
    considerado = df[df["status"] != "cancelado"]
    total_transacoes = int(len(considerado))
    receita_total = float(considerado.loc[considerado["status"] == "pago", "valor"].sum())
    ticket_medio = float(considerado["valor"].mean()) if total_transacoes else 0.0

    inadimplentes = considerado[considerado["status"].isin(INADIMPLENCIA_STATUSES)]
    inadimplencia_valor = float(inadimplentes["valor"].sum())
    valor_total_bruto = float(considerado["valor"].sum())
    taxa_inadimplencia = (
        (inadimplencia_valor / valor_total_bruto) if valor_total_bruto > 0 else 0.0
    )

    periodo_inicio = df["data"].min()
    periodo_fim = df["data"].max()

    return {
        "total_transacoes": total_transacoes,
        "receita_total": round(receita_total, 2),
        "ticket_medio": round(ticket_medio, 2),
        "taxa_inadimplencia": round(taxa_inadimplencia, 4),
        "inadimplencia_valor": round(inadimplencia_valor, 2),
        "periodo_inicio": periodo_inicio.strftime("%Y-%m-%d") if pd.notna(periodo_inicio) else None,
        "periodo_fim": periodo_fim.strftime("%Y-%m-%d") if pd.notna(periodo_fim) else None,
    }


def compute_monthly_timeseries(df: pd.DataFrame) -> list[tuple[str, float, int]]:
    """Agrupa por mês (YYYY-MM) somando receita de transações 'pago' e contando todas."""
    base = df.copy()
    base["periodo"] = base["data"].dt.to_period("M").astype(str)

    receita = (
        base.loc[base["status"] == "pago"]
        .groupby("periodo")["valor"]
        .sum()
        .rename("receita")
    )
    transacoes = base.groupby("periodo")["id"].count().rename("transacoes")

    grouped = pd.concat([receita, transacoes], axis=1).fillna(0).reset_index()
    grouped["receita"] = grouped["receita"].astype(float).round(2)
    grouped["transacoes"] = grouped["transacoes"].astype(int)
    grouped = grouped.sort_values("periodo")

    return [
        (row.periodo, float(row.receita), int(row.transacoes))
        for row in grouped.itertuples(index=False)
    ]

   # Resumo estatístico compacto para enviar ao LLM (sem dados brutos)
def build_llm_summary(df: pd.DataFrame, kpis: dict, timeseries: list[tuple[str, float, int]]) -> dict:
 
    por_status = df.groupby("status")["valor"].agg(["count", "sum"]).round(2).to_dict()
    top_clientes = (
        df.groupby("cliente")["valor"].sum().sort_values(ascending=False).head(5).round(2).to_dict()
    )
    advanced = build_advanced_metrics(df)

    return {
        "kpis": kpis,
        "distribuicao_status": {
            k: {"qtd": int(v["count"]), "soma": float(v["sum"])}
            for k, v in {
                status: {"count": por_status["count"][status], "sum": por_status["sum"][status]}
                for status in por_status["count"].keys()
            }.items()
        },
        "top_clientes_por_valor": {str(k): float(v) for k, v in top_clientes.items()},
        "timeseries_mensal": [
            {"periodo": p, "receita": r, "transacoes": t} for p, r, t in timeseries
        ],
        "metricas_avancadas": advanced,
    }
